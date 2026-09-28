from src.pipeline.dag import DAG
from src.pipeline.task import Task


def _noop(ctx):
    return "ok"


def test_topological_sort():
    dag = DAG(name="test")
    dag.add_task(Task(name="a", func=_noop))
    dag.add_task(Task(name="b", func=_noop, dependencies=["a"]))
    dag.add_task(Task(name="c", func=_noop, dependencies=["a"]))
    dag.add_task(Task(name="d", func=_noop, dependencies=["b", "c"]))

    levels = dag.topological_sort()
    assert levels[0] == ["a"]
    assert set(levels[1]) == {"b", "c"}
    assert levels[2] == ["d"]


def test_validation_missing_dep():
    dag = DAG(name="test")
    dag.add_task(Task(name="a", func=_noop, dependencies=["nonexistent"]))
    errors = dag.validate()
    assert len(errors) > 0


def test_empty_dag():
    dag = DAG(name="empty")
    assert dag.validate() == []
    assert dag.topological_sort() == []
