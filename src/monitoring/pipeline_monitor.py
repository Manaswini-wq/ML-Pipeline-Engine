import json
from pathlib import Path

import numpy as np


class PipelineMonitor:
    """Monitors pipeline execution health."""

    def __init__(self, runs_dir: str = "pipeline_runs") -> None:
        self.dir = Path(runs_dir)

    def get_summary(self) -> dict:
        runs = self._load_runs()
        if not runs:
            return {"total_runs": 0}

        durations = []
        statuses: dict[str, int] = {}
        for r in runs:
            if r.get("end_time") and r.get("start_time"):
                durations.append(r["end_time"] - r["start_time"])
            s = r.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1

        return {
            "total_runs": len(runs),
            "success_rate": statuses.get("completed", 0) / max(len(runs), 1),
            "avg_duration_s": round(np.mean(durations), 2) if durations else 0,
            "p95_duration_s": round(float(np.percentile(durations, 95)), 2) if durations else 0,
            "statuses": statuses,
        }

    def get_task_stats(self) -> dict[str, dict]:
        runs = self._load_runs()
        task_durations: dict[str, list[float]] = {}
        task_failures: dict[str, int] = {}

        for r in runs:
            for name, result in r.get("task_results", {}).items():
                task_durations.setdefault(name, []).append(
                    result.get("duration_seconds", 0)
                )
                if result.get("status") == "failed":
                    task_failures[name] = task_failures.get(name, 0) + 1

        return {
            name: {
                "avg_duration": round(np.mean(durs), 2),
                "max_duration": round(max(durs), 2),
                "failures": task_failures.get(name, 0),
                "runs": len(durs),
            }
            for name, durs in task_durations.items()
        }

    def _load_runs(self) -> list[dict]:
        if not self.dir.exists():
            return []
        return [
            json.loads(p.read_text())
            for p in sorted(self.dir.glob("*.json"))
        ]
