from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelValidator:
    """Quality gates before model promotion.

    Gates:
    1. Minimum AUC threshold
    2. No regression vs current production
    3. Minimum evaluation sample size
    """

    def __init__(self, min_auc: float = 0.65,
                 max_regression: float = 0.01,
                 min_eval_samples: int = 1000) -> None:
        self.min_auc = min_auc
        self.max_regression = max_regression
        self.min_eval_samples = min_eval_samples

    def validate(self, new_metrics: dict,
                 production_metrics: dict | None = None,
                 eval_samples: int = 0) -> tuple[bool, list[str]]:
        """Returns (is_valid, list_of_issues)."""
        issues = []

        new_auc = new_metrics.get("auc", 0)
        if new_auc < self.min_auc:
            issues.append(
                f"AUC {new_auc:.4f} below minimum {self.min_auc}"
            )

        if production_metrics:
            prod_auc = production_metrics.get("auc", 0)
            if prod_auc - new_auc > self.max_regression:
                issues.append(
                    f"Regression: new {new_auc:.4f} vs "
                    f"prod {prod_auc:.4f}"
                )

        if eval_samples < self.min_eval_samples:
            issues.append(
                f"Only {eval_samples} eval samples "
                f"(min: {self.min_eval_samples})"
            )

        is_valid = len(issues) == 0
        if is_valid:
            logger.info("Model passed all validation gates")
        else:
            logger.info(f"Validation failed: {issues}")

        return is_valid, issues
