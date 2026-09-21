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


from src.config import STATISTICS


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

        # 3. Aggregate Expenditures per work (Core Invariants)
        # - WORK_STATUS == "Payment Success" included in total_disbursed
        # - Payment In-Progress excluded from total_disbursed; retained for telemetry/quality
        # - Penny-drop test transactions (<= PENNY_DROP_MAX_AMOUNT) excluded from total_disbursed
        # - Missing expenditure records remain NaN / absent, never silently becoming zero
        exp_agg = pd.DataFrame()
        if not df_expenditures.empty and "WORK_RECOMMENDATION_DTL_ID" in df_expenditures.columns:
            exp_df = df_expenditures.copy()

            # Status classification
            if "WORK_STATUS" in exp_df.columns:
                is_success = exp_df["WORK_STATUS"].astype(str).str.strip() == "Payment Success"
                is_in_progress = exp_df["WORK_STATUS"].astype(str).str.strip() == "Payment In-Progress"
            else:
                is_success = pd.Series(True, index=exp_df.index)
                is_in_progress = pd.Series(False, index=exp_df.index)

            # Penny-drop / validation test transaction detection (<= PENNY_DROP_MAX_AMOUNT INR)
            disb_vals = pd.to_numeric(exp_df["FUND_DISBURSED_AMT"], errors="coerce").fillna(0.0)
            is_penny_drop = disb_vals <= STATISTICS.PENNY_DROP_MAX_AMOUNT

            # Genuine successful disbursements
            exp_df["is_successful_disb"] = is_success & (~is_penny_drop)
            exp_df["is_in_progress_disb"] = is_in_progress
            exp_df["is_penny_drop_disb"] = is_success & is_penny_drop

            # Distinct subsets
            succ_df = exp_df[exp_df["is_successful_disb"]]
            inp_df = exp_df[exp_df["is_in_progress_disb"]]
            penny_df = exp_df[exp_df["is_penny_drop_disb"]]

            # Successful aggregates
            succ_agg = succ_df.groupby("WORK_RECOMMENDATION_DTL_ID").agg(
                total_disbursed=("FUND_DISBURSED_AMT", "sum"),
                payment_count=("FUND_DISBURSED_AMT", "count"),
                first_payment_date=("EXPENDITURE_DATE", "min"),
                last_payment_date=("EXPENDITURE_DATE", "max"),
                vendor_count=("VENDOR_NAME", "nunique"),
                primary_vendor=("VENDOR_NAME", "first"),
                ia_name=("IA_NAME", "first"),
                work_id_exp=("WORK_ID", "first")
            ).reset_index()

            # In-progress telemetry
            inp_agg = inp_df.groupby("WORK_RECOMMENDATION_DTL_ID").agg(
                in_progress_disbursed=("FUND_DISBURSED_AMT", "sum"),
                in_progress_payment_count=("FUND_DISBURSED_AMT", "count")
            ).reset_index()

            # Penny drop telemetry
            penny_agg = penny_df.groupby("WORK_RECOMMENDATION_DTL_ID").agg(
                penny_drop_disbursed=("FUND_DISBURSED_AMT", "sum"),
                penny_drop_count=("FUND_DISBURSED_AMT", "count")
            ).reset_index()

            # Base entity info for works with vouchers (even if no successful payment yet)
            all_exp_works = exp_df.groupby("WORK_RECOMMENDATION_DTL_ID").agg(
                primary_vendor_any=("VENDOR_NAME", "first"),
                ia_name_any=("IA_NAME", "first"),
                work_id_exp_any=("WORK_ID", "first")
            ).reset_index()
            all_exp_works["has_expenditure_record"] = True

            # Merge all aggregates for works with expenditure entries
            exp_agg = pd.merge(all_exp_works, succ_agg, on="WORK_RECOMMENDATION_DTL_ID", how="left")
            exp_agg = pd.merge(exp_agg, inp_agg, on="WORK_RECOMMENDATION_DTL_ID", how="left")
            exp_agg = pd.merge(exp_agg, penny_agg, on="WORK_RECOMMENDATION_DTL_ID", how="left")

            # Fallback for entity names if successful subset was empty
            exp_agg["primary_vendor"] = exp_agg["primary_vendor"].combine_first(exp_agg["primary_vendor_any"])
            exp_agg["ia_name"] = exp_agg["ia_name"].combine_first(exp_agg["ia_name_any"])
            exp_agg["work_id_exp"] = exp_agg["work_id_exp"].combine_first(exp_agg["work_id_exp_any"])
            exp_agg.drop(columns=["primary_vendor_any", "ia_name_any", "work_id_exp_any"], inplace=True)

            # For works with expenditure records but no successful disbursements, total_disbursed is 0.0
            # (indicating zero confirmed disbursements, distinct from missing expenditure which is NaN)
            exp_agg["total_disbursed"] = exp_agg["total_disbursed"].fillna(0.0)
            exp_agg["payment_count"] = exp_agg["payment_count"].fillna(0).astype(int)
            exp_agg["vendor_count"] = exp_agg["vendor_count"].fillna(0).astype(int)
            exp_agg["in_progress_disbursed"] = exp_agg["in_progress_disbursed"].fillna(0.0)
            exp_agg["in_progress_payment_count"] = exp_agg["in_progress_payment_count"].fillna(0).astype(int)
            exp_agg["penny_drop_disbursed"] = exp_agg["penny_drop_disbursed"].fillna(0.0)
            exp_agg["penny_drop_count"] = exp_agg["penny_drop_count"].fillna(0).astype(int)

        if not exp_agg.empty:
            merged = pd.merge(merged, exp_agg, on="WORK_RECOMMENDATION_DTL_ID", how="left")
            merged["has_expenditure_record"] = merged["has_expenditure_record"].fillna(False).astype(bool)
        else:
            merged["has_expenditure_record"] = False
            merged["total_disbursed"] = np.nan
            merged["payment_count"] = np.nan
            merged["first_payment_date"] = pd.NaT
            merged["last_payment_date"] = pd.NaT
            merged["vendor_count"] = 0
            merged["primary_vendor"] = None
            merged["ia_name"] = None
            merged["work_id_exp"] = None
            merged["in_progress_disbursed"] = np.nan
            merged["in_progress_payment_count"] = 0
            merged["penny_drop_disbursed"] = np.nan
            merged["penny_drop_count"] = 0

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
        for dt_col in ["SANCTION_DATE", "RECOMMENDATION_DATE", "first_payment_date", "last_payment_date", "ACTUAL_END_DATE"]:
            if dt_col in merged.columns and not pd.api.types.is_datetime64_any_dtype(merged[dt_col]):
                merged[dt_col] = pd.to_datetime(merged[dt_col], errors="coerce")

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
        is_disbursed = (merged["total_disbursed"].fillna(0.0) > 0) | (merged["payment_count"].fillna(0) > 0)
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
