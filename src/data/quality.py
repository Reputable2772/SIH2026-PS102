"""
MPLADS Data Quality and Coverage Audit Engine.

Evaluates field completeness, computes the Data Quality Index (DQI) per record,
and generates the national 36 State/UT coverage matrix across parliamentary chambers.
"""

from typing import Dict, Tuple
import pandas as pd
import numpy as np


class DataQualityAuditor:
    """Computes multidimensional data quality scores and coverage statistics."""

    @staticmethod
    def compute_work_dqi(df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes an explainable Data Quality Index [0.0, 1.0] for every work.
        Composed of 4 sub-indices:
        1. Identifier Completeness (25%)
        2. Date Integrity (25%)
        3. Financial Validity (25%)
        4. Descriptive Richness (25%)
        """
        df = df.copy()

        # 1. Identifier completeness
        has_rec_id = df["WORK_RECOMMENDATION_DTL_ID"].notna().astype(float)
        has_state = df["STATE_NAME"].notna().astype(float)
        has_ida = df["IDA_NAME"].notna().astype(float)
        id_score = (has_rec_id * 0.5 + has_state * 0.25 + has_ida * 0.25)

        # 2. Date integrity (valid non-negative timeline transitions)
        has_sanc_date = df["SANCTION_DATE"].notna().astype(float)
        valid_rec_sanc = (df["days_rec_to_sanction"].fillna(0) >= 0).astype(float)
        date_score = (has_sanc_date * 0.5 + valid_rec_sanc * 0.5)

        # 3. Financial validity
        valid_sanc_amt = (df["SANCTION_AMOUNT"] > 0).astype(float)
        non_negative_disb = (df["total_disbursed"] >= 0).astype(float)
        fin_score = (valid_sanc_amt * 0.6 + non_negative_disb * 0.4)

        # 4. Descriptive richness
        desc_len = df["WORK_DESCRIPTION"].fillna("").astype(str).str.len()
        desc_score = np.clip(desc_len / 50.0, 0.0, 1.0)

        df["dqi_score"] = (id_score * 0.25 + date_score * 0.25 + fin_score * 0.25 + desc_score * 0.25).round(3)
        return df

    @staticmethod
    def generate_coverage_matrix(df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates aggregate coverage matrix by State/UT and Chamber.
        """
        grp = df.groupby(["STATE_NAME", "house"])
        cov = grp.agg(
            total_works=("WORK_RECOMMENDATION_DTL_ID", "count"),
            completed_works=("ACTUAL_END_DATE", lambda s: s.notna().sum()),
            disbursed_works=("total_disbursed", lambda s: (s > 0).sum()),
            total_sanctioned_amt=("SANCTION_AMOUNT", "sum"),
            total_disbursed_amt=("total_disbursed", "sum"),
            avg_dqi=("dqi_score", "mean"),
            missing_rec_date_pct=("RECOMMENDATION_DATE", lambda s: s.isna().mean() * 100),
            missing_sanc_date_pct=("SANCTION_DATE", lambda s: s.isna().mean() * 100)
        ).reset_index()

        cov["completion_rate_pct"] = (cov["completed_works"] / np.maximum(cov["total_works"], 1) * 100).round(1)
        cov["utilization_rate_pct"] = (cov["total_disbursed_amt"] / np.maximum(cov["total_sanctioned_amt"], 1.0) * 100).round(1)
        cov["avg_dqi"] = cov["avg_dqi"].round(3)
        return cov
