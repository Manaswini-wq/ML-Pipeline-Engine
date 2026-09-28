import hashlib
import shutil
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ArtifactStore:
    """Content-addressable artifact storage using SHA256."""

    def __init__(self, base_dir: str = "artifacts/store") -> None:
        self.dir = Path(base_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def store(self, source_path: str, artifact_name: str) -> str:
        """Store artifact, return content hash."""
        src = Path(source_path)
        content_hash = self._hash(src)
        dest_dir = self.dir / content_hash[:2] / content_hash
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_dir / artifact_name)
        logger.info(f"Stored '{artifact_name}' -> {content_hash[:12]}")
        return content_hash

    def retrieve(self, content_hash: str,
                 artifact_name: str) -> Path | None:
        path = self.dir / content_hash[:2] / content_hash / artifact_name
        return path if path.exists() else None

    def exists(self, content_hash: str) -> bool:
        return (self.dir / content_hash[:2] / content_hash).exists()

    @staticmethod
    def _hash(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
