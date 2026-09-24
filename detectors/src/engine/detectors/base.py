"""
Base Detector and Finding Data Model.

Defines the universal Finding contract mandated by FR-11, FR-12, and AC-19:
Finding + Severity + Confidence + Evidence + Explanation + Next Review Action.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd


class AnomalyCategory(str, Enum):
    COMPLIANCE = "COMPLIANCE"
    FINANCIAL = "FINANCIAL"
    EXECUTION = "EXECUTION"
    AGENCY = "AGENCY"
    NETWORK_SIMILARITY = "NETWORK_SIMILARITY"
    ML_SUPPORTING = "ML_SUPPORTING"


@dataclass
class Finding:
    """Standard explainable finding representation."""

    work_id: str
    detector_code: str
    detector_name: str
    category: AnomalyCategory
    severity: float  # [0.0, 1.0] deviation magnitude
    confidence: float  # [0.0, 1.0] sample & data quality weight
    evidence: Dict[str, Any]  # Observed facts vs baseline
    explanation: str  # Plain-language auditable rationale
    next_review_action: str  # Prescribed administrative next step
    finding_id: Optional[str] = None
    work_rec_id: Optional[str] = None
    state_name: Optional[str] = None
    ida_name: Optional[str] = None
    sanction_amount: float = 0.0

    def __post_init__(self):
        if not self.finding_id:
            h = abs(hash((self.detector_code, self.work_id, self.explanation))) % 1000000
            self.finding_id = f"F_{self.detector_code}_{self.work_id}_{h}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "work_id": self.work_id,
            "work_rec_id": self.work_rec_id,
            "detector_code": self.detector_code,
            "detector_name": self.detector_name,
            "category": self.category.value,
            "severity": round(self.severity, 4),
            "confidence": round(self.confidence, 4),
            "evidence": self.evidence,
            "explanation": self.explanation,
            "next_review_action": self.next_review_action,
            "state_name": self.state_name,
            "ida_name": self.ida_name,
            "sanction_amount": self.sanction_amount,
        }


# Alias for explicit naming
AnomalyFinding = Finding


class BaseDetector:
    """Abstract base class for all modular analytical detectors."""

    def __init__(self, code: str, name: str, category: AnomalyCategory):
        self.code = code
        self.name = name
        self.category = category

    def detect(self, df_works: pd.DataFrame, baseline_engine: Any = None) -> List[Finding]:
        """Executes vector-accelerated detection and yields structured findings."""
        raise NotImplementedError
