"""
Aggregate Trend Analysis Engine.

Calculates temporal velocity, cost escalation, and delay evolution
across financial years, states, and work categories.
"""

import pandas as pd
import numpy as np


class TrendAnalyzer:
    """Computes macroeconomic and operational trend series across MPLADS lifecycles."""

    @staticmethod
    def compute_yearly_trends(df_works: pd.DataFrame) -> pd.DataFrame:
        """Computes annual operational and financial performance indicators."""
        df = df_works.copy()
        if "SANCTION_DATE" not in df.columns or df["SANCTION_DATE"].dropna().empty:
            return pd.DataFrame()

        df["sanction_year"] = df["SANCTION_DATE"].dt.year
        valid = df[df["sanction_year"].notna() & (df["sanction_year"] >= 2020)].copy()

        grp = valid.groupby("sanction_year")
        trends = grp.agg(
            total_sanctioned_works=("WORK_RECOMMENDATION_DTL_ID", "count"),
            total_sanctioned_amount=("SANCTION_AMOUNT", "sum"),
            avg_sanction_amount=("SANCTION_AMOUNT", "mean"),
            avg_sanction_delay=("days_rec_to_sanction", "mean"),
            completion_count=("ACTUAL_END_DATE", lambda s: s.notna().sum()),
            total_disbursed=("total_disbursed", "sum")
        ).reset_index()

        trends["completion_rate_pct"] = (trends["completion_count"] / np.maximum(trends["total_sanctioned_works"], 1) * 100).round(1)
        trends["avg_sanction_delay"] = trends["avg_sanction_delay"].round(1)
        trends["avg_sanction_amount"] = trends["avg_sanction_amount"].round(0)
        return trends

    @staticmethod
    def compute_category_cost_trends(df_works: pd.DataFrame) -> pd.DataFrame:
        """Computes cost dynamics across work categories."""
        df = df_works[df_works["SANCTION_AMOUNT"] > 0].copy()
        if "SANCTION_DATE" in df.columns:
            df["sanction_year"] = df["SANCTION_DATE"].dt.year
            valid = df[df["sanction_year"].notna() & (df["sanction_year"] >= 2022)]
        else:
            valid = df

        grp = valid.groupby(["WORK_CATEGORY", "sanction_year"])
        cat_trends = grp.agg(
            work_count=("WORK_RECOMMENDATION_DTL_ID", "count"),
            median_cost=("SANCTION_AMOUNT", "median"),
            total_cost=("SANCTION_AMOUNT", "sum")
        ).reset_index()

        return cat_trends
