import tempfile
from src.pipeline.dag import DAG
from src.pipeline.task import Task
from src.pipeline.executor import PipelineExecutor


def test_simple_pipeline():
    def step_a(ctx):
        return {"value": 10}

    def step_b(ctx):
        return {"doubled": ctx["step_a"]["value"] * 2}

    dag = DAG(name="test")
    dag.add_task(Task(name="step_a", func=step_a))
    dag.add_task(Task(name="step_b", func=step_b,
                      dependencies=["step_a"]))

    with tempfile.TemporaryDirectory() as tmp:
        executor = PipelineExecutor(checkpoint_dir=tmp)
        run = executor.execute(dag)

    assert run.status == "completed"
    assert run.context["step_b"]["doubled"] == 20


def test_failed_task():
    def failing(ctx):
        raise ValueError("intentional")

    dag = DAG(name="test")
    dag.add_task(Task(name="fail", func=failing))

    with tempfile.TemporaryDirectory() as tmp:
        executor = PipelineExecutor(checkpoint_dir=tmp)
        run = executor.execute(dag)

    assert run.status == "failed"
    assert run.task_results["fail"]["status"] == "failed"
