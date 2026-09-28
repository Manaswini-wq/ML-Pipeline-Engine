import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ModelVersion:
    name: str
    version: str
    path: str
    stage: str = "dev"
    metrics: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    experiment_id: str | None = None


class ModelRegistry:
    """Model versioning, staging, and promotion."""

    def __init__(self, storage_dir: str = "artifacts/registry") -> None:
        self.dir = Path(storage_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.dir / "index.json"
        self._index: dict[str, list[dict]] = self._load_index()

    def register(self, name: str, version: str, source_path: str,
                 metrics: dict | None = None, params: dict | None = None,
                 experiment_id: str | None = None) -> ModelVersion:
        dest = self.dir / name / version
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest / Path(source_path).name)

        mv = ModelVersion(
            name=name, version=version,
            path=str(dest / Path(source_path).name),
            metrics=metrics or {}, params=params or {},
            experiment_id=experiment_id,
        )
        self._index.setdefault(name, []).append(self._to_dict(mv))
        self._save_index()
        logger.info(f"Registered {name} v{version}")
        return mv

    def promote(self, name: str, version: str, stage: str) -> None:
        if stage == "production":
            for v in self._index.get(name, []):
                if v["stage"] == "production":
                    v["stage"] = "archived"

        for v in self._index.get(name, []):
            if v["version"] == version:
                v["stage"] = stage
                break
        self._save_index()
        logger.info(f"Promoted {name} v{version} -> {stage}")

    def get_production_model(self, name: str) -> dict | None:
        for v in self._index.get(name, []):
            if v["stage"] == "production":
                return v
        return None

    def get_latest(self, name: str) -> dict | None:
        versions = self._index.get(name, [])
        return versions[-1] if versions else None

    def list_models(self) -> dict[str, list[dict]]:
        return dict(self._index)

    def list_versions(self, name: str) -> list[dict]:
        return self._index.get(name, [])

    @staticmethod
    def _to_dict(mv: ModelVersion) -> dict:
        return {
            "name": mv.name, "version": mv.version, "path": mv.path,
            "stage": mv.stage, "metrics": mv.metrics, "params": mv.params,
            "created_at": mv.created_at, "experiment_id": mv.experiment_id,
        }

    def _load_index(self) -> dict:
        if self._index_path.exists():
            return json.loads(self._index_path.read_text())
        return {}

    def _save_index(self) -> None:
        self._index_path.write_text(
            json.dumps(self._index, indent=2, default=str)
        )
