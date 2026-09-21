"""
ML Integration and Model Persistence Manager.

Orchestrates training, persistence, and reopening of the composite risk scorer
to incorporate trained ML signals as explainable supporting evidence.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import joblib
import pandas as pd
from src.config import MODELS_DIR, WEIGHTS
from src.engine.detectors.base import Finding
from src.engine.risk.composite_scorer import CompositeRiskScorer, WorkRiskScore
from src.ml.anomaly_ensemble import UnsupervisedAnomalyEnsemble
from src.ml.breach_predictor import SupervisedBreachPredictor


class MLIntegrationManager:
    """Manages the full lifecycle of Phase 4 ML training, serialization, and scorer integration."""

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.anomaly_ensemble = UnsupervisedAnomalyEnsemble()
        self.breach_predictor = SupervisedBreachPredictor()
        self.metadata: Dict[str, Any] = {}

    def train_all(self, df_works: pd.DataFrame) -> Dict[str, Any]:
        """Trains both Component A and Component B models on the real MPLADS dataset."""
        print("Training Component A: Unsupervised Anomaly Ensemble (Isolation Forest)...")
        self.anomaly_ensemble.fit(df_works)

        print("Training Component B: Supervised Breach Predictor (HistGradientBoosting)...")
        eval_metrics = self.breach_predictor.train_and_evaluate(df_works)

        self.metadata = {
            "component_a": {
                "model_type": "Isolation Forest",
                "contamination": self.anomaly_ensemble.contamination,
                "status": "FITTED"
            },
            "component_b": eval_metrics
        }

        # Save model artifacts
        self.save_models()
        return self.metadata

    def save_models(self):
        """Serializes trained model objects and metadata to disk."""
        joblib.dump(self.anomaly_ensemble, self.models_dir / "anomaly_ensemble.joblib")
        joblib.dump(self.breach_predictor, self.models_dir / "breach_predictor.joblib")
        with open(self.models_dir / "ml_metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)

    def load_models(self) -> bool:
        """Loads persisted model artifacts from disk if available."""
        a_path = self.models_dir / "anomaly_ensemble.joblib"
        b_path = self.models_dir / "breach_predictor.joblib"
        meta_path = self.models_dir / "ml_metadata.json"

        if a_path.exists() and b_path.exists():
            self.anomaly_ensemble = joblib.load(a_path)
            self.breach_predictor = joblib.load(b_path)
            if meta_path.exists():
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
            return True
        return False

    def generate_ml_findings(self, df_works: pd.DataFrame) -> List[Finding]:
        """Runs both trained ML models on target works to produce explainable supporting findings."""
        findings: List[Finding] = []
        if self.anomaly_ensemble.is_fitted:
            unsup_findings = self.anomaly_ensemble.detect(df_works, threshold=0.65)
            findings.extend(unsup_findings)

        if self.breach_predictor.is_fitted:
            breach_findings = self.breach_predictor.detect_in_progress_risks(df_works, threshold=0.65)
            findings.extend(breach_findings)

        return findings

    def score_works_integrated(
        self,
        df_works: pd.DataFrame,
        rule_findings: List[Finding],
        ml_findings: Optional[List[Finding]] = None
    ) -> List[WorkRiskScore]:
        """
        Reopens the Phase 3 composite scorer to add trained ML signals alongside rule/statistical signals.
        """
        all_findings = list(rule_findings)
        if ml_findings:
            all_findings.extend(ml_findings)

        scorer = CompositeRiskScorer(weights=WEIGHTS)
        return scorer.score_works(df_works, all_findings)
