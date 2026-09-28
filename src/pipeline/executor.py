import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.pipeline.dag import DAG
from src.pipeline.task import TaskStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineRun:
    run_id: str
    dag_name: str
    status: str = "running"
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    task_results: dict[str, dict] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


class PipelineExecutor:
    """Executes a DAG with parallel task execution per level."""

    def __init__(self, max_workers: int = 4,
                 checkpoint_dir: str = "pipeline_runs") -> None:
        self.max_workers = max_workers
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, dag: DAG,
                context: dict[str, Any] | None = None) -> PipelineRun:
        """Execute all tasks respecting dependency order."""
        errors = dag.validate()
        if errors:
            raise ValueError(f"Invalid DAG: {errors}")

        run_id = f"run_{dag.name}_{int(time.time())}"
        run = PipelineRun(run_id=run_id, dag_name=dag.name,
                          context=context or {})

        logger.info(f"Starting pipeline: {run_id}")
        levels = dag.topological_sort()

        for level_idx, level in enumerate(levels):
            logger.info(f"Level {level_idx}: {level}")

            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                futures = {}
                for task_name in level:
                    task = dag.tasks[task_name]
                    future = pool.submit(task.execute, run.context)
                    futures[future] = task_name

                for future in as_completed(futures):
                    task_name = futures[future]
                    result = future.result()
                    run.task_results[task_name] = {
                        "status": result.status.value,
                        "duration_seconds": round(result.duration_seconds, 2),
                        "error": result.error,
                    }
                    if result.output is not None:
                        run.context[task_name] = result.output

                    if result.status == TaskStatus.FAILED:
                        logger.info(f"FAILED: {task_name}: {result.error}")
                    else:
                        logger.info(
                            f"OK: {task_name} ({result.duration_seconds:.2f}s)"
                        )

            failed = [
                n for n, r in run.task_results.items()
                if r["status"] == "failed"
            ]
            if failed:
                run.status = "failed"
                logger.info(f"Pipeline failed at: {failed}")
                break

        if run.status != "failed":
            run.status = "completed"

        run.end_time = time.time()
        self._save_run(run)
        duration = run.end_time - run.start_time
        logger.info(f"Pipeline {run_id}: {run.status} ({duration:.2f}s)")
        return run

    def _save_run(self, run: PipelineRun) -> None:
        path = self.checkpoint_dir / f"{run.run_id}.json"
        data = {
            "run_id": run.run_id,
            "dag_name": run.dag_name,
            "status": run.status,
            "start_time": run.start_time,
            "end_time": run.end_time,
            "task_results": run.task_results,
        }
        path.write_text(json.dumps(data, indent=2, default=str))

    def list_runs(self) -> list[dict]:
        return [
            json.loads(p.read_text())
            for p in sorted(self.checkpoint_dir.glob("*.json"))
        ]
