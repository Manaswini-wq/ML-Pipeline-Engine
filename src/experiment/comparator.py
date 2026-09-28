import pandas as pd


class ExperimentComparator:
    """Compares metrics across experiments."""

    @staticmethod
    def compare(experiments: list[dict],
                metrics: list[str] | None = None) -> pd.DataFrame:
        rows = []
        for exp in experiments:
            row = {
                "experiment_id": exp["id"],
                "name": exp["name"],
                "status": exp.get("status", "unknown"),
            }
            row.update(exp.get("params", {}))
            exp_metrics = exp.get("metrics", {})
            if metrics:
                row.update({m: exp_metrics.get(m) for m in metrics})
            else:
                row.update(exp_metrics)
            rows.append(row)
        return pd.DataFrame(rows)

    @staticmethod
    def find_best(experiments: list[dict], metric: str,
                  higher_is_better: bool = True) -> dict | None:
        valid = [
            e for e in experiments if metric in e.get("metrics", {})
        ]
        if not valid:
            return None
        return sorted(
            valid, key=lambda e: e["metrics"][metric],
            reverse=higher_is_better,
        )[0]
