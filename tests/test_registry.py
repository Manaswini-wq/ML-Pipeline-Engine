import os
import tempfile
from src.registry.model_registry import ModelRegistry


def test_register_and_promote():
    with tempfile.TemporaryDirectory() as tmp:
        registry = ModelRegistry(storage_dir=tmp)

        model_path = os.path.join(tmp, "dummy.joblib")
        with open(model_path, "w") as f:
            f.write("model_data")

        registry.register("test_model", "v1", model_path,
                          metrics={"auc": 0.85})
        registry.register("test_model", "v2", model_path,
                          metrics={"auc": 0.87})

        versions = registry.list_versions("test_model")
        assert len(versions) == 2

        registry.promote("test_model", "v2", "production")
        prod = registry.get_production_model("test_model")
        assert prod["version"] == "v2"
        assert prod["stage"] == "production"


def test_auto_archive_old_production():
    with tempfile.TemporaryDirectory() as tmp:
        registry = ModelRegistry(storage_dir=tmp)

        model_path = os.path.join(tmp, "dummy.joblib")
        with open(model_path, "w") as f:
            f.write("data")

        registry.register("m", "v1", model_path)
        registry.register("m", "v2", model_path)
        registry.promote("m", "v1", "production")
        registry.promote("m", "v2", "production")

        versions = registry.list_versions("m")
        v1 = next(v for v in versions if v["version"] == "v1")
        v2 = next(v for v in versions if v["version"] == "v2")
        assert v1["stage"] == "archived"
        assert v2["stage"] == "production"
