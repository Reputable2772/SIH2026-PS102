"""
Supervised Breach-Risk Predictive Model (Component B).

Predicts future milestone SLA breach probabilities for currently in-progress works
using strictly sanction-time observable features, temporal holdouts, and observation windows.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, confusion_matrix, precision_score, recall_score, roc_auc_score

from src.engine.detectors.base import AnomalyCategory, Finding
from src.ml.features import FeaturePipeline


class SupervisedBreachPredictor:
    """Component B: Predictive breach-risk model trained on real lifecycle outcomes."""

    def __init__(self, random_state: int = 42):
        self.code = "ML-BREACH-02"
        self.name = "Predictive Breach-Risk Model"
        self.category = AnomalyCategory.ML_SUPPORTING
        self.random_state = random_state
        self.model = HistGradientBoostingClassifier(
            max_iter=100, learning_rate=0.1, max_depth=5, random_state=self.random_state
        )
        self.state_freq_map: Dict[str, float] = {}
        self.cat_freq_map: Dict[str, float] = {}
        self.evaluation_metrics: Dict[str, Any] = {}
        self.is_fitted = False

    def train_and_evaluate(self, df_works: pd.DataFrame, split_date: Optional[pd.Timestamp] = None) -> Dict[str, Any]:
        """
        Executes rigorous temporal-holdout training and validation:
        1. Filters works to observation window eligibility (>= 365 days old).
        2. Splits by temporal holdout: Earlier sanctions (Train), Later sanctions (Test).
        3. Trains on sanction-time features only.
        4. Reports concrete AUC-ROC, Precision, Recall, PR-AUC, and Confusion Matrix.
        """
        eligible_df, labels = FeaturePipeline.construct_breach_labels(df_works)
        if len(eligible_df) < 100:
            raise ValueError(f"Insufficient eligible works ({len(eligible_df)}) for robust ML training.")

        eligible_df["breach_label"] = labels

        # Ensure SANCTION_DATE is coerced to datetime
        eligible_df["SANCTION_DATE"] = pd.to_datetime(eligible_df["SANCTION_DATE"], errors="coerce")

        if split_date is not None and not isinstance(split_date, pd.Timestamp):
            split_date = pd.to_datetime(split_date)

        # Determine temporal split date (default: 70th percentile of valid sanction dates)
        sanc_valid = eligible_df["SANCTION_DATE"].dropna()
        if split_date is None and not sanc_valid.empty:
            split_date = sanc_valid.quantile(0.70)

        # Temporal split on SANCTION_DATE
        if split_date is not None and not sanc_valid.empty:
            train_mask = eligible_df["SANCTION_DATE"] < split_date
            test_mask = eligible_df["SANCTION_DATE"] >= split_date
        else:
            train_mask = pd.Series(False, index=eligible_df.index)
            test_mask = pd.Series(False, index=eligible_df.index)

        # Fallback to random 70/30 split if temporal cohort has extreme imbalance or too small test set
        if train_mask.sum() < 50 or test_mask.sum() < 50:
            np.random.seed(self.random_state)
            rand_split = np.random.rand(len(eligible_df)) < 0.70
            train_mask = rand_split
            test_mask = ~rand_split

        train_df = eligible_df[train_mask]
        test_df = eligible_df[test_mask]

        # Extract sanction-time features
        X_train, self.state_freq_map, self.cat_freq_map = FeaturePipeline.build_sanction_time_features(train_df)
        y_train = train_df["breach_label"].values

        X_test, _, _ = FeaturePipeline.build_sanction_time_features(
            test_df, state_freq_map=self.state_freq_map, cat_freq_map=self.cat_freq_map
        )
        y_test = test_df["breach_label"].values

        # Fit model
        self.model.fit(X_train, y_train)
        self.is_fitted = True

        # Evaluate on holdout
        y_prob = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.50).astype(int)

        auc_roc = float(roc_auc_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else 0.50
        pr_auc = float(average_precision_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else 0.50
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        cm = confusion_matrix(y_test, y_pred).tolist()
        class_prevalence = float(np.mean(y_test))

        self.evaluation_metrics = {
            "train_samples": int(len(train_df)),
            "test_samples": int(len(test_df)),
            "class_prevalence": round(class_prevalence, 4),
            "auc_roc": round(auc_roc, 4),
            "pr_auc": round(pr_auc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "confusion_matrix": cm,
            "status": "PASS" if auc_roc >= 0.65 else "WARNING",
        }
        return self.evaluation_metrics

    def predict_breach_probability(self, df_works: pd.DataFrame) -> np.ndarray:
        """Predicts breach probabilities for works using strictly sanction-time features."""
        if not self.is_fitted:
            raise ValueError("Model must be trained before predicting breach risk.")
        X, _, _ = FeaturePipeline.build_sanction_time_features(
            df_works, state_freq_map=self.state_freq_map, cat_freq_map=self.cat_freq_map
        )
        return self.model.predict_proba(X)[:, 1]

    def detect_in_progress_risks(self, df_works: pd.DataFrame, threshold: float = 0.70) -> List[Finding]:
        """
        Applies model to currently in-progress works to produce early-warning findings.
        """
        if not self.is_fitted:
            return []

        # Target ongoing works
        sanc_col = pd.to_datetime(df_works.get("SANCTION_DATE"), errors="coerce")
        comp_col = pd.to_datetime(df_works.get("ACTUAL_END_DATE"), errors="coerce")
        ongoing = df_works[comp_col.isna() & sanc_col.notna()].copy()
        if ongoing.empty:
            return []

        probs = self.predict_breach_probability(ongoing)
        flagged_idx = np.where(probs >= threshold)[0]

        findings: List[Finding] = []
        for idx in flagged_idx:
            row = ongoing.iloc[idx]
            prob = float(probs[idx])

            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
            work_id = str(row.get("WORK_ID") or rec_id)

            f = Finding(
                finding_id=f"FIND-ML-BREACH-{rec_id}",
                work_id=work_id,
                work_rec_id=rec_id,
                detector_code=self.code,
                detector_name=self.name,
                category=self.category,
                severity=prob,
                confidence=0.85,
                evidence={
                    "model_type": "Gradient Boosting Early-Warning Classifier",
                    "predicted_breach_probability": round(prob, 4),
                    "holdout_auc_roc": self.evaluation_metrics.get("auc_roc"),
                    "sanction_amount": float(row.get("SANCTION_AMOUNT", 0.0)),
                    "days_rec_to_sanction": float(row.get("days_rec_to_sanction", 0.0)),
                    "state_name": str(row.get("STATE_NAME")),
                    "work_category": str(row.get("WORK_CATEGORY")),
                },
                explanation=(
                    f"Predictive model flags {prob:.1%} probability of statutory execution breach based on sanction-time "
                    f"profile (State baseline, category historical delay rate, and proposal approval turnaround)."
                ),
                next_review_action=(
                    "Implement proactive project oversight: establish bi-weekly milestone checkpoints with Implementing "
                    "Agency to mitigate forecasted execution stall."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0)),
            )
            findings.append(f)

        return findings
