"""
MPLADS Intelligence Engine — Core Analytical Package.

Exposes the unified high-level programmatic interface (MPLADSEngine) along with
modular components for baselines, rule detectors, cross-work intelligence, risk scoring,
dossier generation, and ML integration.
"""

from src.engine.baselines import BaselineEngine
from src.engine.coordinator import DetectionResultSet, MPLADSEngine
from src.engine.cross_work import CrossWorkIntelligenceEngine
from src.engine.detectors import AnomalyCategory, AnomalyFinding, CoreDetectionEngine
from src.engine.risk.composite_scorer import CompositeRiskScorer, ReviewPriority, WorkRiskScore
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
