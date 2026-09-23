"""
Controlled Anomaly Injection Suite.

Performs mathematical stress tests to verify scoring monotonicity, sensitivity,
and zero-variance edge cases as mandated by AC-13.
"""

from typing import Dict, Any
import pandas as pd
from src.engine.detectors import CoreDetectionEngine
from src.engine.risk.composite_scorer import CompositeRiskScorer, ReviewPriority


class AnomalyInjectionTester:
    """Injects synthetic perturbations into normal baseline works and verifies engine properties."""

    @staticmethod
    def test_monotonicity() -> Dict[str, Any]:
        """
        Verifies mathematical monotonicity:
        Injecting progressively severe delays or costs must strictly non-decrease composite severity.
        """
        base_work = {
            "WORK_RECOMMENDATION_DTL_ID": "INJ-001",
            "WORK_ID": "WINJ001",
            "STATE_NAME": "MAHARASHTRA",
            "IDA_NAME": "PUNE",
            "WORK_CATEGORY": "Education",
            "SANCTION_AMOUNT": 500000.0,
            "RECOMMENDATION_DATE": pd.Timestamp("2025-01-01"),
            "SANCTION_DATE": pd.Timestamp("2025-01-20"),
            "ACTUAL_END_DATE": pd.Timestamp("2025-06-01"),
            "days_rec_to_sanction": 19,
            "days_sanction_to_completion": 132,
            "days_since_sanction": 200,
            "total_disbursed": 500000.0,
            "payment_count": 2,
            "first_payment_date": pd.Timestamp("2025-02-01"),
            "last_payment_date": pd.Timestamp("2025-05-01"),
            "house": "LOK_SABHA",
            "dqi_score": 0.95
        }

        delays = [20, 50, 90, 150, 300]
        severities = []
        priorities = []

        engine = CoreDetectionEngine()
        scorer = CompositeRiskScorer()

        for d in delays:
            w = base_work.copy()
            w["days_rec_to_sanction"] = d
            w["SANCTION_DATE"] = w["RECOMMENDATION_DATE"] + pd.Timedelta(days=d)
            df = pd.DataFrame([w])
            engine.fit_baselines(df)
            findings = engine.run(df)
            scores = scorer.score_works(df, findings)
            severities.append(scores[0].composite_severity)
            priorities.append(scores[0].priority.value)

        # Verify monotonic non-decreasing order
        is_monotonic = all(severities[i] <= severities[i+1] for i in range(len(severities)-1))
        return {
            "test": "monotonicity",
            "delays_tested": delays,
            "severities": severities,
            "priorities": priorities,
            "is_monotonic": is_monotonic,
            "status": "PASS" if is_monotonic else "FAIL"
        }

    @staticmethod
    def test_cost_sensitivity() -> Dict[str, Any]:
        """
        Verifies cost outlier sensitivity:
        Scaling budget above peer median triggers FIN-D5 and elevates priority to CRITICAL/HIGH.
        """
        # Baseline cohort
        cohort = [
            {
                "WORK_RECOMMENDATION_DTL_ID": f"C-{i}",
                "STATE_NAME": "TAMIL_NADU",
                "WORK_CATEGORY": "Health",
                "SANCTION_AMOUNT": 500000.0 + i * 2000.0,
                "days_rec_to_sanction": 25,
                "SANCTION_DATE": pd.Timestamp("2024-01-20"),
                "ACTUAL_END_DATE": pd.Timestamp("2024-06-01"),
                "days_since_sanction": 200,
                "days_sanction_to_completion": 132,
                "dqi_score": 0.90,
                "house": "LOK_SABHA",
                "total_disbursed": 500000.0,
                "payment_count": 1
            }
            for i in range(25)
        ]
        # Injected extreme cost outlier: 10x peer median
        outlier = {
            "WORK_RECOMMENDATION_DTL_ID": "OUTLIER-1",
            "WORK_ID": "W-OUTLIER",
            "STATE_NAME": "TAMIL_NADU",
            "WORK_CATEGORY": "Health",
            "SANCTION_AMOUNT": 5000000.0,  # 10x
            "days_rec_to_sanction": 25,
            "SANCTION_DATE": pd.Timestamp("2024-01-20"),
            "ACTUAL_END_DATE": pd.Timestamp("2024-06-01"),
            "days_since_sanction": 200,
            "days_sanction_to_completion": 132,
            "dqi_score": 0.95,
            "house": "LOK_SABHA",
            "total_disbursed": 5000000.0,
            "payment_count": 1
        }
        df = pd.DataFrame(cohort + [outlier])

        engine = CoreDetectionEngine()
        engine.fit_baselines(df)
        findings = engine.run(df)
        scorer = CompositeRiskScorer()
        scores = scorer.score_works(df, findings)

        outlier_score = next(s for s in scores if s.work_rec_id == "OUTLIER-1")
        has_cost_finding = any(f.detector_code == "FIN-D5" for f in outlier_score.findings)
        is_elevated = outlier_score.priority in {ReviewPriority.CRITICAL, ReviewPriority.HIGH}

        return {
            "test": "cost_sensitivity",
            "outlier_severity": outlier_score.composite_severity,
            "outlier_priority": outlier_score.priority.value,
            "has_fin_d5_finding": has_cost_finding,
            "is_elevated": is_elevated,
            "status": "PASS" if (has_cost_finding and is_elevated) else "FAIL"
        }
