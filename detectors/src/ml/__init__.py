"""
Machine Learning & Advanced Analytics Package (Phase 4).

Provides feature engineering, unsupervised anomaly ensemble, supervised breach predictor,
and integrated composite scoring.
"""

from src.ml.anomaly_ensemble import UnsupervisedAnomalyEnsemble
from src.ml.breach_predictor import SupervisedBreachPredictor
from src.ml.features import FeaturePipeline
from src.ml.integration import MLIntegrationManager

__all__ = ["FeaturePipeline", "UnsupervisedAnomalyEnsemble", "SupervisedBreachPredictor", "MLIntegrationManager"]
