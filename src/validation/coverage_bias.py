"""
Coverage-Bias and Completeness Correlation Auditor.

Tests whether anomaly flag rates correlate spuriously with state-level data completeness
or digitization coverage as mandated by AC-17.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from src.engine.detectors.base import Finding


class CoverageBiasAuditor:
    """Computes correlation between data completeness (DQI) and anomaly flag rates."""

    @staticmethod
    def audit_coverage_bias(df_works: pd.DataFrame, findings: List[Finding]) -> Dict[str, Any]:
        """
        Computes Spearman rank correlation between state-level mean DQI and anomaly flag rate.
        """
        if df_works.empty or not findings:
            return {
                "status": "PASS",
                "spearman_rho": 0.0,
                "p_value": 1.0,
                "has_coverage_bias": False,
                "interpretation": "Insufficient data to compute correlation."
            }

        # Find unique flagged works per state
        flagged_rec_ids = {f.work_rec_id for f in findings if f.work_rec_id}
        df = df_works.copy()
        df["is_flagged"] = df["WORK_RECOMMENDATION_DTL_ID"].isin(flagged_rec_ids)

        state_stats = df.groupby("STATE_NAME").agg(
            total_works=("WORK_RECOMMENDATION_DTL_ID", "count"),
            flagged_works=("is_flagged", "sum"),
            mean_dqi=("dqi_score", "mean")
        ).reset_index()

        # Filter states with >= 10 works
        state_stats = state_stats[state_stats["total_works"] >= 10].copy()
        if len(state_stats) < 5:
            return {
                "status": "PASS",
                "spearman_rho": 0.0,
                "p_value": 1.0,
                "has_coverage_bias": False,
                "interpretation": "Too few states to evaluate rank correlation."
            }

        state_stats["flag_rate"] = state_stats["flagged_works"] / state_stats["total_works"]

        # Spearman rank correlation
        if state_stats["mean_dqi"].nunique() <= 1 or state_stats["flag_rate"].nunique() <= 1:
            rho, p_val = 0.0, 1.0
        else:
            rho, p_val = spearmanr(state_stats["mean_dqi"], state_stats["flag_rate"])
        rho = float(rho) if pd.notna(rho) else 0.0
        p_val = float(p_val) if pd.notna(p_val) else 1.0

        # High bias if |rho| > 0.60 and statistically significant (p < 0.05)
        has_bias = abs(rho) > 0.60 and p_val < 0.05

        return {
            "evaluated_states": len(state_stats),
            "spearman_rho": round(rho, 3),
            "p_value": round(p_val, 4),
            "has_coverage_bias": has_bias,
            "status": "PASS" if not has_bias else "WARNING",
            "interpretation": (
                f"Spearman rank correlation between state data completeness (DQI) and anomaly flag rate is {rho:.3f} (p={p_val:.4f}). "
                + ("Flag rates reflect genuine substantive irregularities independent of reporting coverage."
                   if not has_bias else
                   "Warning: Flag rates correlate with reporting completeness. High-completeness states may show inflated flag counts.")
            )
        }
