"""
Composite Risk Scoring Engine.

Combines independent detector findings into orthogonal Severity and Confidence axes,
applies statutory policy overrides, and classifies works into actionable review priority tiers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import numpy as np
import pandas as pd
from src.config import WEIGHTS
from src.engine.detectors.base import Finding, AnomalyCategory


class ReviewPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NORMAL = "NORMAL"


@dataclass
class WorkRiskScore:
    """Two-axis risk assessment for a single work entity."""
    work_id: str
    work_rec_id: str
    composite_severity: float  # [0.0, 1.0]
    composite_confidence: float# [0.0, 1.0]
    priority: ReviewPriority
    findings_count: int
    findings: List[Finding]
    category_severities: Dict[str, float]
    has_statutory_breach: bool
    state_name: Optional[str] = None
    ida_name: Optional[str] = None
    sanction_amount: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_id": self.work_id,
            "work_rec_id": self.work_rec_id,
            "composite_severity": round(self.composite_severity, 4),
            "composite_confidence": round(self.composite_confidence, 4),
            "priority": self.priority.value,
            "findings_count": self.findings_count,
            "has_statutory_breach": self.has_statutory_breach,
            "category_severities": {k: round(v, 4) for k, v in self.category_severities.items()},
            "state_name": self.state_name,
            "ida_name": self.ida_name,
            "sanction_amount": self.sanction_amount,
            "finding_codes": [f.detector_code for f in self.findings]
        }


class CompositeRiskScorer:
    """Aggregates findings into two-axis risk profiles with statutory overrides."""

    def __init__(self, weights: object = WEIGHTS):
        self.weights = weights

    def score_works(self, df_works: pd.DataFrame, findings: List[Finding]) -> List[WorkRiskScore]:
        # Group findings by work recommendation ID
        findings_by_work: Dict[str, List[Finding]] = defaultdict(list)
        for f in findings:
            if f.work_rec_id:
                findings_by_work[f.work_rec_id].append(f)

        work_scores: List[WorkRiskScore] = []
        for _, row in df_works.iterrows():
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
            work_id = str(row.get("WORK_ID") or rec_id)
            w_findings = findings_by_work.get(rec_id, [])

            if not w_findings:
                # Normal unflagged work
                work_scores.append(WorkRiskScore(
                    work_id=work_id,
                    work_rec_id=rec_id,
                    composite_severity=0.0,
                    composite_confidence=float(row.get("dqi_score", 1.0)),
                    priority=ReviewPriority.NORMAL,
                    findings_count=0,
                    findings=[],
                    category_severities={},
                    has_statutory_breach=False,
                    state_name=row.get("STATE_NAME"),
                    ida_name=row.get("IDA_NAME"),
                    sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0))
                ))
                continue

            # Compute category-wise maximum severity
            cat_severities: Dict[str, float] = defaultdict(float)
            cat_confidences: Dict[str, float] = defaultdict(float)
            has_statutory = False

            for f in w_findings:
                cat = f.category.value
                cat_severities[cat] = max(cat_severities[cat], f.severity)
                cat_confidences[cat] = max(cat_confidences[cat], f.confidence)
            statutory_count = sum(1 for f in w_findings if f.detector_code in {"COMP-D1", "COMP-D2", "COMP-D3", "COMP-D4"})
            if statutory_count >= 1 and any(f.severity >= 0.65 for f in w_findings if f.category == AnomalyCategory.COMPLIANCE):
                has_statutory = True

            # Composite severity: 70% driven by the most severe anomaly category,
            # 30% driven by cross-category breadth accumulation across the risk spectrum
            max_cat_sev = max(cat_severities.values()) if cat_severities else 0.0
            cat_weights_map = {
                AnomalyCategory.COMPLIANCE.value: self.weights.WEIGHT_COMPLIANCE,
                AnomalyCategory.FINANCIAL.value: self.weights.WEIGHT_FINANCIAL,
                AnomalyCategory.EXECUTION.value: self.weights.WEIGHT_EXECUTION,
                AnomalyCategory.AGENCY.value: 0.15,
                AnomalyCategory.NETWORK_SIMILARITY.value: 0.15,
                AnomalyCategory.ML_SUPPORTING.value: 0.15,
            }
            ref_weight_scale = self.weights.WEIGHT_COMPLIANCE + self.weights.WEIGHT_FINANCIAL
            weighted_sum = sum(cat_severities[cat] * cat_weights_map.get(cat, 0.1) for cat in cat_severities)
            breadth_term = min(1.0, weighted_sum / ref_weight_scale) if ref_weight_scale > 0 else 0.0

            comp_sev = min(1.0, 0.70 * max_cat_sev + 0.30 * breadth_term)

            # Composite confidence (harmonic mean between average finding confidence and DQI)
            avg_find_conf = np.mean([f.confidence for f in w_findings]) if w_findings else 0.5
            dqi = float(row.get("dqi_score", 0.8))
            comp_conf = float(2 * (avg_find_conf * dqi) / (avg_find_conf + dqi + 1e-6))

            # Priority classification with Statutory Override
            if has_statutory and comp_sev >= 0.60:
                priority = ReviewPriority.CRITICAL
            elif statutory_count >= 2 or (statutory_count >= 1 and comp_sev >= 0.45):
                # Multiple statutory compliance breaches or significant legal breach
                priority = ReviewPriority.HIGH
            elif comp_sev >= 0.70 and comp_conf >= 0.50:
                priority = ReviewPriority.CRITICAL
            elif comp_sev >= 0.50 and comp_conf >= 0.40:
                priority = ReviewPriority.HIGH
            elif comp_sev >= 0.30:
                priority = ReviewPriority.MEDIUM
            else:
                priority = ReviewPriority.LOW

            work_scores.append(WorkRiskScore(
                work_id=work_id,
                work_rec_id=rec_id,
                composite_severity=comp_sev,
                composite_confidence=comp_conf,
                priority=priority,
                findings_count=len(w_findings),
                findings=w_findings,
                category_severities=dict(cat_severities),
                has_statutory_breach=has_statutory,
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0))
            ))

        return work_scores
