"""
Entity Recurrence Anomaly Engine.

Tracks repeated appearances of the same Implementing Agencies or Vendors
across multiple independent anomaly findings.
"""

from typing import List, Dict, Optional
from collections import defaultdict
import pandas as pd
from src.engine.detectors.base import Finding, AnomalyCategory


class EntityRecurrenceDetector:
    """Surfaces systemic compliance or financial risk when entities recur across anomaly types."""

    def __init__(self, min_anomalies: int = 3):
        self.code = "REC-D15"
        self.name = "Systemic Entity Anomaly Recurrence"
        self.category = AnomalyCategory.AGENCY
        self.min_anomalies = min_anomalies

    def detect(self, df_works: pd.DataFrame, prior_findings: List[Finding]) -> List[Finding]:
        if not prior_findings:
            return []

        # Map findings to works
        rec_to_findings: Dict[str, List[Finding]] = defaultdict(list)
        for f in prior_findings:
            if f.work_rec_id:
                rec_to_findings[f.work_rec_id].append(f)

        work_dict = {
            str(r["WORK_RECOMMENDATION_DTL_ID"]): r
            for _, r in df_works.iterrows()
            if pd.notna(r.get("WORK_RECOMMENDATION_DTL_ID"))
        }

        # Track IA and Vendor finding counts
        ia_findings: Dict[str, List[Finding]] = defaultdict(list)
        v_findings: Dict[str, List[Finding]] = defaultdict(list)

        for rec_id, f_list in rec_to_findings.items():
            if rec_id in work_dict:
                w = work_dict[rec_id]
                ia = w.get("ia_name")
                if ia and pd.notna(ia):
                    ia_findings[str(ia)].extend(f_list)
                v = w.get("primary_vendor")
                if v and pd.notna(v):
                    v_findings[str(v)].extend(f_list)

        recurrence_findings: List[Finding] = []

        # Check IAs
        for ia, f_list in ia_findings.items():
            unique_works = len({f.work_rec_id for f in f_list if f.work_rec_id})
            if unique_works >= self.min_anomalies:
                codes = sorted(list({f.detector_code for f in f_list}))
                sample_finding = f_list[0]
                rec_id = str(sample_finding.work_rec_id)
                work_id = str(sample_finding.work_id)

                f = Finding(
                    finding_id=f"FIND-D15-IA-{abs(hash(ia)) % 100000}",
                    work_id=work_id,
                    work_rec_id=rec_id,
                    detector_code=self.code,
                    detector_name=self.name,
                    category=self.category,
                    severity=min(1.0, 0.5 + (unique_works - 3) * 0.1),
                    confidence=0.90,
                    evidence={
                        "entity_type": "IMPLEMENTING_AGENCY",
                        "entity_name": ia,
                        "flagged_works_count": unique_works,
                        "associated_anomaly_types": codes
                    },
                    explanation=(
                        f"Implementing Agency '{ia}' is involved in {unique_works} distinct anomalous works across "
                        f"multiple categories ({', '.join(codes)}). Indicates systemic execution pathology."
                    ),
                    next_review_action=(
                        "Trigger institutional performance review of this Implementing Agency by State Nodal Department."
                    ),
                    state_name=sample_finding.state_name,
                    ida_name=sample_finding.ida_name,
                    sanction_amount=sample_finding.sanction_amount
                )
                recurrence_findings.append(f)

        return recurrence_findings
