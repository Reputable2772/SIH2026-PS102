"""
Cross-Work and Pattern Intelligence Package.

Provides similarity / duplicate work detection, agency & vendor concentration analysis,
systemic entity recurrence, and aggregate trend tracking.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from src.engine.detectors.base import Finding
from src.engine.cross_work.similarity import DuplicateWorkDetector
from src.engine.cross_work.concentration import AgencyConcentrationDetector, VendorConcentrationDetector
from src.engine.cross_work.recurrence import EntityRecurrenceDetector
from src.engine.cross_work.trends import TrendAnalyzer


class CrossWorkIntelligenceEngine:
    """Orchestrates all Phase 2 cross-work and relational pattern analytics."""

    def __init__(self):
        self.similarity_detector = DuplicateWorkDetector()
        self.agency_detector = AgencyConcentrationDetector()
        self.vendor_detector = VendorConcentrationDetector()
        self.recurrence_detector = EntityRecurrenceDetector()
        self.trend_analyzer = TrendAnalyzer()

    def run(self, df_works: pd.DataFrame, prior_findings: Optional[List[Finding]] = None) -> List[Finding]:
        """Runs all Phase 2 pattern analytics; strictly deterministic, zero ML."""
        findings: List[Finding] = []

        # 1. Duplicate & Similarity detection
        sim_findings = self.similarity_detector.detect(df_works)
        findings.extend(sim_findings)

        # 2. IA Concentration
        ia_findings = self.agency_detector.detect(df_works)
        findings.extend(ia_findings)

        # 3. Vendor Concentration
        v_findings = self.vendor_detector.detect(df_works)
        findings.extend(v_findings)

        # 4. Entity Recurrence across anomalies
        if prior_findings:
            rec_findings = self.recurrence_detector.detect(df_works, prior_findings)
            findings.extend(rec_findings)

        return findings
