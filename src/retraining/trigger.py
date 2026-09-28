import time

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RetrainingTrigger:
    """Determines when retraining should be triggered.

    Conditions:
    1. Performance degradation (AUC drop)
    2. Model staleness (age in days)
    3. Manual trigger
    """

    def __init__(self, performance_threshold: float = 0.02,
                 staleness_days: int = 7) -> None:
        self.performance_threshold = performance_threshold
        self.staleness_days = staleness_days

    def should_retrain(self, current_metrics: dict,
                       baseline_metrics: dict,
                       model_created_at: float) -> tuple[bool, str]:
        """Check if retraining is needed.

        Returns (should_retrain, reason).
        """
        current_auc = current_metrics.get("auc", 0)
        baseline_auc = baseline_metrics.get("auc", 0)
        if baseline_auc - current_auc > self.performance_threshold:
            reason = (f"Performance degraded: AUC dropped from "
                      f"{baseline_auc:.4f} to {current_auc:.4f}")
            logger.info(reason)
            return True, reason

        age_days = (time.time() - model_created_at) / 86400
        if age_days > self.staleness_days:
            reason = (f"Model is {age_days:.1f} days old "
                      f"(limit: {self.staleness_days})")
            logger.info(reason)
            return True, reason

        return False, "No retraining needed"
