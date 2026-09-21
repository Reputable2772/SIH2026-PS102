"""
Canonical Work Reconstruction and Lifecycle State Engine.

Reconstructs the primary analytical entity (Work) across the e-SAKSHI lifecycle:
Recommendation -> Sanction -> Execution -> Progress -> Payments -> Completion.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np


class LifecycleStage:
    RECOMMENDED = "RECOMMENDED"
    SANCTIONED = "SANCTIONED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    IRREGULAR = "IRREGULAR"


class WorkLifecycleReconstructor:
    """Combines normalized datasets into unified, canonical Work records."""

    def __init__(self, snapshot_date: Optional[pd.Timestamp] = None):
        # Default snapshot date matching recent e-SAKSHI data snapshot (2026-09-21)
        self.snapshot_date = snapshot_date or pd.Timestamp("2026-09-21")

    def reconstruct(
        self,
        df_recommended: pd.DataFrame,
        df_sanctioned: pd.DataFrame,
        df_expenditures: pd.DataFrame,
        df_completed: pd.DataFrame,
        house: str = "lok_sabha"
    ) -> pd.DataFrame:
        """
        Performs relational linkage and canonical work synthesis.
        """
        # 1. Start with Sanctioned as the anchor of legal project existence
        sanc = df_sanctioned.copy()
        sanc["house"] = house

        # 2. Merge Recommended data
        rec_cols = [
            "WORK_RECOMMENDATION_DTL_ID",
            "RECOMMENDATION_DATE",
            "RECOMMENDED_AMOUNT"
        ]
        rec_subset = df_recommended[[c for c in rec_cols if c in df_recommended.columns]].drop_duplicates(
            subset=["WORK_RECOMMENDATION_DTL_ID"]
        )
        
        merged = pd.merge(
            sanc,
            rec_subset,
            on="WORK_RECOMMENDATION_DTL_ID",
            how="left",
            suffixes=("", "_rec")
        )

        # Ensure RECOMMENDATION_DATE priority
        if "RECOMMENDATION_DATE_rec" in merged.columns:
            merged["RECOMMENDATION_DATE"] = merged["RECOMMENDATION_DATE"].combine_first(merged["RECOMMENDATION_DATE_rec"])
            merged.drop(columns=["RECOMMENDATION_DATE_rec"], inplace=True)

        # 3. Aggregate Expenditures per work
        exp_agg = pd.DataFrame()
        if not df_expenditures.empty and "WORK_RECOMMENDATION_DTL_ID" in df_expenditures.columns:
            exp_grp = df_expenditures.groupby("WORK_RECOMMENDATION_DTL_ID")
            exp_agg = exp_grp.agg(
                total_disbursed=("FUND_DISBURSED_AMT", "sum"),
                payment_count=("FUND_DISBURSED_AMT", "count"),
                first_payment_date=("EXPENDITURE_DATE", "min"),
                last_payment_date=("EXPENDITURE_DATE", "max"),
                vendor_count=("VENDOR_NAME", "nunique"),
                primary_vendor=("VENDOR_NAME", "first"),
                ia_name=("IA_NAME", "first"),
                work_id_exp=("WORK_ID", "first")
            ).reset_index()

        if not exp_agg.empty:
            merged = pd.merge(merged, exp_agg, on="WORK_RECOMMENDATION_DTL_ID", how="left")
        else:
            merged["total_disbursed"] = 0.0
            merged["payment_count"] = 0
            merged["first_payment_date"] = pd.NaT
            merged["last_payment_date"] = pd.NaT
            merged["vendor_count"] = 0
            merged["primary_vendor"] = None
            merged["ia_name"] = None
            merged["work_id_exp"] = None

        # Fill missing expenditure metrics
        merged["total_disbursed"] = merged["total_disbursed"].fillna(0.0)
        merged["payment_count"] = merged["payment_count"].fillna(0).astype(int)
        merged["vendor_count"] = merged["vendor_count"].fillna(0).astype(int)

        # 4. Merge Completed works
        comp_cols = [
            "WORK_RECOMMENDATION_DTL_ID",
            "ACTUAL_AMOUNT",
            "ACTUAL_END_DATE",
            "AVERAGE_RATING",
            "WORK_ID"
        ]
        comp_subset = df_completed[[c for c in comp_cols if c in df_completed.columns]].drop_duplicates(
            subset=["WORK_RECOMMENDATION_DTL_ID"]
        )
        
        merged = pd.merge(
            merged,
            comp_subset,
            on="WORK_RECOMMENDATION_DTL_ID",
            how="left",
            suffixes=("", "_comp")
        )

        # Resolve WORK_ID across sanctioned, expenditure, and completed
        if "WORK_ID_comp" in merged.columns:
            merged["WORK_ID"] = merged["WORK_ID"].combine_first(merged["WORK_ID_comp"])
            merged.drop(columns=["WORK_ID_comp"], inplace=True)
        if "work_id_exp" in merged.columns:
            merged["WORK_ID"] = merged["WORK_ID"].combine_first(merged["work_id_exp"])
            merged.drop(columns=["work_id_exp"], inplace=True)

        # 5. Compute Lifecycle Durations (in calendar days)
        merged["days_rec_to_sanction"] = (
            merged["SANCTION_DATE"] - merged["RECOMMENDATION_DATE"]
        ).dt.days

        merged["days_sanction_to_first_payment"] = (
            merged["first_payment_date"] - merged["SANCTION_DATE"]
        ).dt.days

        merged["days_sanction_to_completion"] = (
            merged["ACTUAL_END_DATE"] - merged["SANCTION_DATE"]
        ).dt.days

        merged["days_since_sanction"] = (
            self.snapshot_date - merged["SANCTION_DATE"]
        ).dt.days

        # 6. Determine Canonical Lifecycle Stage
        is_completed = merged["ACTUAL_END_DATE"].notna() | (merged["ACTUAL_AMOUNT"] > 0)
        is_disbursed = (merged["total_disbursed"] > 0) | (merged["payment_count"] > 0)
        is_sanctioned = merged["SANCTION_DATE"].notna() | (merged["SANCTION_AMOUNT"] > 0)

        conditions = [
            is_completed,
            is_disbursed,
            is_sanctioned
        ]
        choices = [
            LifecycleStage.COMPLETED,
            LifecycleStage.IN_PROGRESS,
            LifecycleStage.SANCTIONED
        ]
        merged["lifecycle_stage"] = np.select(conditions, choices, default=LifecycleStage.RECOMMENDED)

        # Detect lifecycle sequence anomalies
        merged["is_retroactive_sanction"] = merged["days_rec_to_sanction"] < 0
        merged["is_completion_before_sanction"] = merged["days_sanction_to_completion"] < 0
        merged["is_disbursement_before_sanction"] = merged["days_sanction_to_first_payment"] < 0

        return merged
