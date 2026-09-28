from pydantic_settings import BaseSettings
from pydantic import Field


class PipelineConfig(BaseSettings):
    max_parallel_tasks: int = Field(default=4)
    checkpoint_dir: str = Field(default="pipeline_runs")
    default_timeout_seconds: int = Field(default=600)
    model_config = {"env_prefix": "PIPELINE_"}


class ExperimentConfig(BaseSettings):
    storage_dir: str = Field(default="experiments")
    model_config = {"env_prefix": "EXPERIMENT_"}


class RegistryConfig(BaseSettings):
    storage_dir: str = Field(default="artifacts/registry")
    model_config = {"env_prefix": "REGISTRY_"}


class RetrainingConfig(BaseSettings):
    performance_threshold: float = Field(default=0.02)
    staleness_days: int = Field(default=7)
    model_config = {"env_prefix": "RETRAIN_"}


class AppConfig:
    def __init__(self) -> None:
        self.pipeline = PipelineConfig()
        self.experiment = ExperimentConfig()
        self.registry = RegistryConfig()
        self.retraining = RetrainingConfig()
