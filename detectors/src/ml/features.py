"""
ML Feature Engineering and Leakage Prevention Pipeline.

Enforces strict separation between sanction-time predictive features and
full lifecycle features for unsupervised anomaly detection.
"""

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.config import POLICY


class FeaturePipeline:
    """Prepares sanitized numerical feature matrices with strict temporal integrity."""

    # Features knowable at or before sanction approval
    SANCTION_TIME_FEATURES = [
        "log_sanction_amount",
        "days_rec_to_sanction_clean",
        "is_lok_sabha",
        "state_freq",
        "cat_freq",
        "dqi_score",
    ]

    # Lifecycle features for unsupervised anomaly discovery
    LIFECYCLE_ANOMALY_FEATURES = [
        "log_sanction_amount",
        "log_disbursed_amount",
        "payment_count",
        "days_rec_to_sanction_clean",
        "days_to_first_payment_clean",
        "disbursement_ratio",
        "dqi_score",
    ]

    @classmethod
    def build_sanction_time_features(
        cls,
        df_works: pd.DataFrame,
        state_freq_map: Optional[Dict[str, float]] = None,
        cat_freq_map: Optional[Dict[str, float]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, float], Dict[str, float]]:
        """
        Extracts features strictly knowable at or before sanction time.
        Guarantees zero data leakage from execution, payment, or completion stages.
        """
        df = df_works.copy()

        # 1. Log-transformed sanction budget
        amt = pd.to_numeric(df["SANCTION_AMOUNT"], errors="coerce").fillna(0.0)
        df["log_sanction_amount"] = np.log1p(np.maximum(amt, 0.0))

        # 2. Recommendation turnaround
        if "days_rec_to_sanction" not in df.columns or not pd.api.types.is_numeric_dtype(df["days_rec_to_sanction"]):
            if "SANCTION_DATE" in df.columns and "RECOMMENDATION_DATE" in df.columns:
                sanc = pd.to_datetime(df["SANCTION_DATE"], errors="coerce")
                rec = pd.to_datetime(df["RECOMMENDATION_DATE"], errors="coerce")
                rec_days = (sanc - rec).dt.days.fillna(30.0)
            else:
                rec_days = pd.Series(30.0, index=df.index)
        else:
            rec_days = pd.to_numeric(df["days_rec_to_sanction"], errors="coerce").fillna(30.0)
        df["days_rec_to_sanction_clean"] = np.clip(rec_days, 0.0, 365.0)

        # 3. Chamber binary flag
        df["is_lok_sabha"] = (df["house"] == "LOK_SABHA").astype(float)

        # 4. Frequency encodings
        if state_freq_map is None:
            s_counts = df["STATE_NAME"].value_counts(normalize=True).to_dict()
            state_freq_map = {str(k): float(v) for k, v in s_counts.items()}
        df["state_freq"] = df["STATE_NAME"].astype(str).map(state_freq_map).fillna(0.01)

        if cat_freq_map is None:
            c_counts = df["WORK_CATEGORY"].value_counts(normalize=True).to_dict()
            cat_freq_map = {str(k): float(v) for k, v in c_counts.items()}
        df["cat_freq"] = df["WORK_CATEGORY"].astype(str).map(cat_freq_map).fillna(0.01)

        # 5. DQI
        df["dqi_score"] = pd.to_numeric(df.get("dqi_score", 0.8), errors="coerce").fillna(0.8)

        X = df[cls.SANCTION_TIME_FEATURES].fillna(0.0)
        return X, state_freq_map, cat_freq_map

    @classmethod
    def build_lifecycle_anomaly_features(cls, df_works: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts multi-stage lifecycle features for unsupervised anomaly ensemble training.
        """
        df = df_works.copy()

        sanc = pd.to_numeric(df.get("SANCTION_AMOUNT", 0.0), errors="coerce").fillna(0.0)
        disb = pd.to_numeric(df.get("total_disbursed", 0.0), errors="coerce").fillna(0.0)
        cnt = pd.to_numeric(df.get("payment_count", 0.0), errors="coerce").fillna(0.0)

        df["log_sanction_amount"] = np.log1p(np.maximum(sanc, 0.0))
        df["log_disbursed_amount"] = np.log1p(np.maximum(disb, 0.0))
        df["payment_count"] = np.clip(cnt, 0.0, 50.0)

        rec_days = pd.to_numeric(df.get("days_rec_to_sanction", 30.0), errors="coerce").fillna(30.0)
        df["days_rec_to_sanction_clean"] = np.clip(rec_days, 0.0, 365.0)

        pay_days = pd.to_numeric(df.get("days_sanction_to_first_payment", 90.0), errors="coerce").fillna(90.0)
        df["days_to_first_payment_clean"] = np.clip(pay_days, 0.0, 365.0)

        df["disbursement_ratio"] = np.clip(disb / np.maximum(sanc, 1.0), 0.0, 3.0)
        df["dqi_score"] = pd.to_numeric(df.get("dqi_score", 0.8), errors="coerce").fillna(0.8)

        X = df[cls.LIFECYCLE_ANOMALY_FEATURES].fillna(0.0)
        return X

    @classmethod
    def construct_breach_labels(
        cls,
        df_works: pd.DataFrame,
        observation_window_ls: int = POLICY.EXECUTION_SLA_DAYS,
        observation_window_rs: int = POLICY.RS_POST_TENURE_SLA_DAYS,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Constructs ground-truth breach outcome labels strictly for works whose elapsed age
        exceeds the statutory observation window. Excludes immature works entirely.
        """
        df = df_works.copy()

        # Ensure days_since_sanction is present and numeric
        if "days_since_sanction" not in df.columns or not pd.api.types.is_numeric_dtype(df["days_since_sanction"]):
            sanc = pd.to_datetime(df.get("SANCTION_DATE"), errors="coerce")
            df["days_since_sanction"] = (pd.Timestamp.now() - sanc).dt.days.fillna(0.0)
        else:
            df["days_since_sanction"] = pd.to_numeric(df["days_since_sanction"], errors="coerce").fillna(0.0)

        if "days_sanction_to_completion" not in df.columns or not pd.api.types.is_numeric_dtype(
            df["days_sanction_to_completion"]
        ):
            sanc = pd.to_datetime(df.get("SANCTION_DATE"), errors="coerce")
            comp = pd.to_datetime(df.get("ACTUAL_END_DATE"), errors="coerce")
            df["days_sanction_to_completion"] = (comp - sanc).dt.days.fillna(0.0)
        else:
            df["days_sanction_to_completion"] = pd.to_numeric(
                df["days_sanction_to_completion"], errors="coerce"
            ).fillna(0.0)

        # Observation eligibility check: work age must exceed statutory completion SLA
        is_rs = df["house"] == "RAJYA_SABHA"
        req_window = np.where(is_rs, observation_window_rs, observation_window_ls)
        is_eligible = df["days_since_sanction"] >= req_window

        eligible_df = df[is_eligible].copy()
        if eligible_df.empty:
            return eligible_df, pd.Series(dtype=int)

        # Label: breached = 1 if completion exceeded SLA or if work is still incomplete past SLA
        comp_date = pd.to_datetime(eligible_df.get("ACTUAL_END_DATE"), errors="coerce")
        is_comp = comp_date.notna()
        sla = np.where(eligible_df["house"] == "RAJYA_SABHA", observation_window_rs, observation_window_ls)

        completed_breach = is_comp & (eligible_df["days_sanction_to_completion"] > sla)
        ongoing_breach = (~is_comp) & (eligible_df["days_since_sanction"] > sla)

        labels = (completed_breach | ongoing_breach).astype(int)
        return eligible_df, labels
