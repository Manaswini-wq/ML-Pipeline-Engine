import json
import time
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExperimentTracker:
    """Tracks ML experiments as JSON files."""

    def __init__(self, storage_dir: str = "experiments") -> None:
        self.dir = Path(storage_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def create_experiment(self, name: str, params: dict,
                          tags: dict | None = None) -> str:
        exp_id = f"{name}_{int(time.time())}"
        experiment = {
            "id": exp_id, "name": name,
            "params": params, "tags": tags or {},
            "metrics": {}, "artifacts": {},
            "created_at": time.time(), "status": "running",
        }
        self._save(exp_id, experiment)
        logger.info(f"Created experiment: {exp_id}")
        return exp_id

    def log_metrics(self, exp_id: str, metrics: dict[str, float]) -> None:
        exp = self._load(exp_id)
        exp["metrics"].update(metrics)
        self._save(exp_id, exp)

    def log_artifact(self, exp_id: str, name: str, path: str) -> None:
        exp = self._load(exp_id)
        exp["artifacts"][name] = path
        self._save(exp_id, exp)

    def complete(self, exp_id: str) -> None:
        exp = self._load(exp_id)
        exp["status"] = "completed"
        exp["completed_at"] = time.time()
        self._save(exp_id, exp)

    def get_experiment(self, exp_id: str) -> dict:
        return self._load(exp_id)

    def list_experiments(self) -> list[dict]:
        return [
            json.loads(p.read_text())
            for p in sorted(self.dir.glob("*.json"))
        ]

    def get_best(self, metric: str,
                 higher_is_better: bool = True) -> dict | None:
        exps = [
            e for e in self.list_experiments()
            if metric in e.get("metrics", {})
        ]
        if not exps:
            return None
        return sorted(
            exps, key=lambda e: e["metrics"][metric],
            reverse=higher_is_better,
        )[0]

    def _save(self, exp_id: str, data: dict) -> None:
        (self.dir / f"{exp_id}.json").write_text(
            json.dumps(data, indent=2, default=str)
        )

    def _load(self, exp_id: str) -> dict:
        return json.loads((self.dir / f"{exp_id}.json").read_text())
