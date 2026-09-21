"""
Detection Engine Package.

Provides universal access to all modular detectors and batch execution orchestrator.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from src.engine.detectors.base import BaseDetector, Finding, AnomalyFinding, AnomalyCategory
from src.engine.detectors.compliance import (
    SanctionSLABreachDetector,
    ExecutionDeadlineDetector,
    StalledDisbursementDetector,
    LifecycleLeapDetector
)
from src.engine.detectors.financial import (
    CostPeerOutlierDetector,
    CostOverrunDetector,
    TemporalDisbursementSpikeDetector
)
from src.engine.detectors.execution import ProgressExpenditureMismatchDetector
from src.engine.detectors.agency import IAOverloadDetector
from src.engine.baselines import BaselineEngine


class CoreDetectionEngine:
    """Orchestrates all Phase 1 core detectors against canonical works."""

    def __init__(self, baseline_engine: Optional[BaselineEngine] = None):
        self.baseline_engine = baseline_engine or BaselineEngine()
        self.detectors: List[BaseDetector] = [
            SanctionSLABreachDetector(),
            ExecutionDeadlineDetector(),
            StalledDisbursementDetector(),
            LifecycleLeapDetector(),
            CostPeerOutlierDetector(),
            CostOverrunDetector(),
            TemporalDisbursementSpikeDetector(),
            ProgressExpenditureMismatchDetector(),
            IAOverloadDetector()
        ]

    def fit_baselines(self, df_works: pd.DataFrame) -> "CoreDetectionEngine":
        """Fits statistical peer baselines."""
        self.baseline_engine.fit(df_works)
        return self

    def run(self, df_works: pd.DataFrame) -> List[Finding]:
        """Runs all enabled detectors and aggregates findings."""
        all_findings: List[Finding] = []
        for det in self.detectors:
            try:
                findings = det.detect(df_works, baseline_engine=self.baseline_engine)
                all_findings.extend(findings)
            except Exception as e:
                print(f"Warning: Detector {det.code} ({det.name}) encountered error: {e}")
        return all_findings


__all__ = [
    "CoreDetectionEngine",
    "Finding",
    "AnomalyFinding",
    "AnomalyCategory",
    "BaseDetector",
]
