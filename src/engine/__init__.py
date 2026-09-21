"""
MPLADS Intelligence Engine — Core Analytical Package.

Exposes the unified high-level programmatic interface (MPLADSEngine) along with
modular components for baselines, rule detectors, cross-work intelligence, risk scoring,
dossier generation, and ML integration.
"""

from src.engine.coordinator import MPLADSEngine, DetectionResultSet
from src.engine.baselines import BaselineEngine
from src.engine.detectors import CoreDetectionEngine, AnomalyFinding, AnomalyCategory
from src.engine.cross_work import CrossWorkIntelligenceEngine
from src.engine.risk.composite_scorer import CompositeRiskScorer, WorkRiskScore, ReviewPriority
from src.engine.risk.dossier import DossierBuilder, GovernanceDossier

__all__ = [
    "MPLADSEngine",
    "DetectionResultSet",
    "BaselineEngine",
    "CoreDetectionEngine",
    "AnomalyFinding",
    "AnomalyCategory",
    "CrossWorkIntelligenceEngine",
    "CompositeRiskScorer",
    "WorkRiskScore",
    "ReviewPriority",
    "DossierBuilder",
    "GovernanceDossier",
]
