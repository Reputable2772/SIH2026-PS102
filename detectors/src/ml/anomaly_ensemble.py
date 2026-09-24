"""
Unsupervised Anomaly Ensemble (Component A).

Trains an Isolation Forest on empirical multi-stage lifecycle feature vectors to discover
unusual multidimensional irregularities not captured by individual univariate rules.
"""

from typing import List

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from src.engine.detectors.base import AnomalyCategory, Finding
from src.ml.features import FeaturePipeline


class UnsupervisedAnomalyEnsemble:
    """Component A: Isolation Forest Anomaly Ensemble on real MPLADS data."""

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.code = "ML-UNSUP-01"
        self.name = "Multivariate Anomaly Ensemble"
        self.category = AnomalyCategory.ML_SUPPORTING
        self.contamination = contamination
        self.random_state = random_state
        self.scaler = RobustScaler()
        self.model = IsolationForest(
            contamination=self.contamination, random_state=self.random_state, n_estimators=100, n_jobs=-1
        )
        self.is_fitted = False

    def fit(self, df_works: pd.DataFrame) -> "UnsupervisedAnomalyEnsemble":
        """Fits the anomaly ensemble on real Phase 0 features."""
        X = FeaturePipeline.build_lifecycle_anomaly_features(df_works)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        return self

    def predict_anomaly_scores(self, df_works: pd.DataFrame) -> np.ndarray:
        """Computes calibrated anomaly probabilities [0.0, 1.0]."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before predicting anomaly scores.")
        X = FeaturePipeline.build_lifecycle_anomaly_features(df_works)
        X_scaled = self.scaler.transform(X)
        # Raw decision function: lower = more anomalous
        raw_scores = self.model.decision_function(X_scaled)
        # Normalize into [0.0, 1.0] where 1.0 = highly anomalous
        # Sigmoidal inversion calibration
        calibrated = 1.0 / (1.0 + np.exp(raw_scores * 8.0))
        return np.clip(calibrated, 0.0, 1.0)

    def detect(self, df_works: pd.DataFrame, threshold: float = 0.65) -> List[Finding]:
        """Generates explainable findings for works exceeding anomaly probability threshold."""
        if not self.is_fitted:
            self.fit(df_works)

        scores = self.predict_anomaly_scores(df_works)
        flagged_indices = np.where(scores >= threshold)[0]

        findings: List[Finding] = []
        for idx in flagged_indices:
            row = df_works.iloc[idx]
            score = float(scores[idx])

            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
            work_id = str(row.get("WORK_ID") or rec_id)

            f = Finding(
                finding_id=f"FIND-ML-UNSUP-{rec_id}",
                work_id=work_id,
                work_rec_id=rec_id,
                detector_code=self.code,
                detector_name=self.name,
                category=self.category,
                severity=score,
                confidence=0.80,
                evidence={
                    "model_type": "Isolation Forest Ensemble",
                    "calibrated_anomaly_score": round(score, 4),
                    "features_analyzed": FeaturePipeline.LIFECYCLE_ANOMALY_FEATURES,
                    "sanction_amount": float(row.get("SANCTION_AMOUNT", 0.0)),
                    "total_disbursed": float(row.get("total_disbursed", 0.0)),
                    "days_rec_to_sanction": float(row.get("days_rec_to_sanction", 0.0)),
                },
                explanation=(
                    f"Work exhibits an atypical combination of budget scale, disbursement velocity, and turnaround milestones "
                    f"(Anomaly Score: {score:.1%}), isolated by multivariate decision tree partitioning."
                ),
                next_review_action=(
                    "Perform multi-signal holistic audit of project files to cross-check whether atypical financial "
                    "drawdowns correspond to legitimate specialized engineering requirements."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0)),
            )
            findings.append(f)

        return findings
