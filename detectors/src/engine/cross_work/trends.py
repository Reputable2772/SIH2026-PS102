"""
Aggregate Trend Analysis Engine.

Calculates temporal velocity, cost escalation, and delay evolution
across financial years, states, and work categories.
"""

import numpy as np
import pandas as pd


class TrendAnalyzer:
    """Computes macroeconomic and operational trend series across MPLADS lifecycles."""

    @staticmethod
    def compute_yearly_trends(df_works: pd.DataFrame) -> pd.DataFrame:
        """Computes annual operational and financial performance indicators."""
        df = df_works.copy()
        if "SANCTION_DATE" not in df.columns or df["SANCTION_DATE"].dropna().empty:
            return pd.DataFrame()

        if not pd.api.types.is_datetime64_any_dtype(df["SANCTION_DATE"]):
            df["SANCTION_DATE"] = pd.to_datetime(df["SANCTION_DATE"], errors="coerce")

        df["sanction_year"] = df["SANCTION_DATE"].dt.year
        valid = df[df["sanction_year"].notna() & (df["sanction_year"] >= 2020)].copy()

        grp = valid.groupby("sanction_year")
        trends = grp.agg(
            total_sanctioned_works=("WORK_RECOMMENDATION_DTL_ID", "count"),
            total_sanctioned_amount=("SANCTION_AMOUNT", "sum"),
            avg_sanction_amount=("SANCTION_AMOUNT", "mean"),
            avg_sanction_delay=("days_rec_to_sanction", "mean"),
            completion_count=("ACTUAL_END_DATE", lambda s: s.notna().sum()),
            total_disbursed=("total_disbursed", "sum"),
        ).reset_index()

        trends["completion_rate_pct"] = (
            trends["completion_count"] / np.maximum(trends["total_sanctioned_works"], 1) * 100
        ).round(1)
        trends["avg_sanction_delay"] = trends["avg_sanction_delay"].round(1)
        trends["avg_sanction_amount"] = trends["avg_sanction_amount"].round(0)
        return trends
