import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from sklearn.datasets import make_classification
from sklearn.metrics import roc_auc_score, log_loss

from src.pipeline.dag import DAG
from src.pipeline.task import Task
from src.pipeline.executor import PipelineExecutor
from src.registry.model_registry import ModelRegistry
from src.retraining.validator import ModelValidator


def task_generate_data(context: dict) -> dict:
    X, y = make_classification(
        n_samples=10000, n_features=20, n_informative=12,
        n_redundant=4, random_state=42,
    )
    split = int(len(X) * 0.7)
    val_split = int(len(X) * 0.85)
    return {
        "X_train": X[:split], "y_train": y[:split],
        "X_val": X[split:val_split], "y_val": y[split:val_split],
        "X_test": X[val_split:], "y_test": y[val_split:],
    }


def task_train_lightgbm(context: dict) -> dict:
    import lightgbm as lgb
    data = context["generate_data"]
    train_set = lgb.Dataset(data["X_train"], label=data["y_train"])
    val_set = lgb.Dataset(data["X_val"], label=data["y_val"])
    model = lgb.train(
        {"objective": "binary", "metric": "binary_logloss",
         "learning_rate": 0.05, "num_leaves": 63, "verbose": -1},
        train_set, num_boost_round=200,
        valid_sets=[train_set, val_set],
        callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)],
    )
    return {"model": model, "model_type": "lightgbm"}


def task_train_logistic(context: dict) -> dict:
    from sklearn.linear_model import LogisticRegression
    data = context["generate_data"]
    model = LogisticRegression(max_iter=1000)
    model.fit(data["X_train"], data["y_train"])
    return {"model": model, "model_type": "logistic"}


def task_evaluate(context: dict) -> dict:
    data = context["generate_data"]
    results = {}
    for task_name in ["train_lightgbm", "train_logistic"]:
        if task_name not in context:
            continue
        info = context[task_name]
        model = info["model"]
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(data["X_test"])[:, 1]
        else:
            proba = model.predict(data["X_test"])
        results[info["model_type"]] = {
            "auc": roc_auc_score(data["y_test"], proba),
            "logloss": log_loss(data["y_test"], proba),
        }
    best = max(results.items(), key=lambda x: x[1]["auc"])
    return {
        "all_results": results,
        "best_model": best[0],
        "best_metrics": best[1],
    }


def task_register(context: dict) -> dict:
    import joblib
    eval_result = context["evaluate"]
    best_name = eval_result["best_model"]
    best_metrics = eval_result["best_metrics"]

    validator = ModelValidator(min_auc=0.60)
    is_valid, issues = validator.validate(
        new_metrics=best_metrics, eval_samples=1500,
    )
    if not is_valid:
        return {"registered": False, "issues": issues}

    model = context[f"train_{best_name}"]["model"]
    os.makedirs("artifacts", exist_ok=True)
    path = f"artifacts/{best_name}_model.joblib"
    joblib.dump(model, path)

    registry = ModelRegistry()
    version = f"v{int(time.time())}"
    registry.register(
        name="classifier", version=version, source_path=path,
        metrics=best_metrics, params={"model_type": best_name},
    )
    registry.promote("classifier", version, "production")
    return {
        "registered": True,
        "version": version,
        "metrics": best_metrics,
    }


def main() -> None:
    dag = DAG(name="ml_training_pipeline")
    dag.add_task(Task(name="generate_data", func=task_generate_data))
    dag.add_task(Task(name="train_lightgbm", func=task_train_lightgbm,
                      dependencies=["generate_data"]))
    dag.add_task(Task(name="train_logistic", func=task_train_logistic,
                      dependencies=["generate_data"]))
    dag.add_task(Task(name="evaluate", func=task_evaluate,
                      dependencies=["train_lightgbm", "train_logistic"]))
    dag.add_task(Task(name="register", func=task_register,
                      dependencies=["evaluate"]))

    print("Pipeline DAG:")
    for level in dag.topological_sort():
        print(f"  {level}")

    executor = PipelineExecutor(max_workers=2)
    run = executor.execute(dag)

    print(f"\nPipeline {run.run_id}: {run.status}")
    for name, result in run.task_results.items():
        print(f"  {name}: {result['status']} ({result['duration_seconds']}s)")

    if "register" in run.context:
        reg = run.context["register"]
        if reg.get("registered"):
            print(f"\nBest model: {reg['version']}")
            print(f"  Metrics: {reg['metrics']}")


if __name__ == "__main__":
    main()
