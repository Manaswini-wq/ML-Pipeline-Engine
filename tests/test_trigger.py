import time
from src.retraining.trigger import RetrainingTrigger
from src.retraining.validator import ModelValidator


def test_performance_trigger():
    trigger = RetrainingTrigger(performance_threshold=0.02)
    should, reason = trigger.should_retrain(
        current_metrics={"auc": 0.80},
        baseline_metrics={"auc": 0.85},
        model_created_at=time.time(),
    )
    assert should is True
    assert "degraded" in reason


def test_staleness_trigger():
    trigger = RetrainingTrigger(staleness_days=7)
    should, reason = trigger.should_retrain(
        current_metrics={"auc": 0.85},
        baseline_metrics={"auc": 0.85},
        model_created_at=time.time() - 86400 * 10,
    )
    assert should is True
    assert "days old" in reason


def test_no_retrain():
    trigger = RetrainingTrigger()
    should, _ = trigger.should_retrain(
        current_metrics={"auc": 0.85},
        baseline_metrics={"auc": 0.85},
        model_created_at=time.time(),
    )
    assert should is False


def test_validator_pass():
    validator = ModelValidator(min_auc=0.65)
    valid, issues = validator.validate(
        new_metrics={"auc": 0.70}, eval_samples=2000,
    )
    assert valid is True
    assert len(issues) == 0


def test_validator_fail():
    validator = ModelValidator(min_auc=0.65)
    valid, issues = validator.validate(
        new_metrics={"auc": 0.50}, eval_samples=500,
    )
    assert valid is False
    assert len(issues) == 2
