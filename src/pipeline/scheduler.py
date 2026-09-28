import time
from typing import Callable

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineScheduler:
    """Interval-based pipeline scheduling."""

    def __init__(self) -> None:
        self._schedules: list[dict] = []

    def add_schedule(self, name: str, pipeline_func: Callable,
                     interval_hours: float = 24) -> None:
        self._schedules.append({
            "name": name,
            "func": pipeline_func,
            "interval_hours": interval_hours,
            "last_run": 0.0,
        })
        logger.info(f"Scheduled '{name}' every {interval_hours}h")

    def check_and_run(self) -> list[str]:
        """Run any pipelines that are due. Returns names triggered."""
        triggered = []
        now = time.time()
        for s in self._schedules:
            elapsed = (now - s["last_run"]) / 3600
            if elapsed >= s["interval_hours"]:
                logger.info(f"Triggering: {s['name']}")
                try:
                    s["func"]()
                    s["last_run"] = now
                    triggered.append(s["name"])
                except Exception as e:
                    logger.info(f"Failed: {s['name']}: {e}")
        return triggered

    def list_schedules(self) -> list[dict]:
        return [
            {"name": s["name"], "interval_hours": s["interval_hours"],
             "last_run": s["last_run"]}
            for s in self._schedules
        ]
