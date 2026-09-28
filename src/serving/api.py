import time

from fastapi import FastAPI, HTTPException

from src.pipeline.executor import PipelineExecutor
from src.experiment.tracker import ExperimentTracker
from src.registry.model_registry import ModelRegistry

app = FastAPI(title="ML Pipeline Platform", version="1.0.0")

executor = PipelineExecutor()
tracker = ExperimentTracker()
registry = ModelRegistry()
start_time = time.time()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - start_time, 1),
    }


@app.get("/pipelines")
async def list_pipelines():
    return {"runs": executor.list_runs()}


@app.get("/pipelines/{run_id}")
async def get_pipeline(run_id: str):
    runs = executor.list_runs()
    run = next((r for r in runs if r["run_id"] == run_id), None)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@app.get("/experiments")
async def list_experiments():
    return {"experiments": tracker.list_experiments()}


@app.get("/experiments/{exp_id}")
async def get_experiment(exp_id: str):
    try:
        return tracker.get_experiment(exp_id)
    except FileNotFoundError:
        raise HTTPException(404, "Experiment not found")


@app.get("/models")
async def list_models():
    return {"models": registry.list_models()}


@app.get("/models/{name}/versions")
async def list_versions(name: str):
    return {"versions": registry.list_versions(name)}


@app.post("/models/{name}/promote")
async def promote_model(name: str, version: str,
                        stage: str = "production"):
    try:
        registry.promote(name, version, stage)
        return {"status": "promoted", "name": name,
                "version": version, "stage": stage}
    except Exception as e:
        raise HTTPException(500, str(e))
