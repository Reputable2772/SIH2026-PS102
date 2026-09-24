"""
Explainable Review Dossier Generator.

Synthesizes multi-detector findings into a structured administrative dossier answering
the 5 Core Governance Questions mandated by FR-12 and provides actionable review next-steps.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from src.engine.risk.composite_scorer import WorkRiskScore


@dataclass
class GovernanceDossier:
    """Standard audit and review dossier for human oversight."""

    work_id: str
    work_rec_id: str
    priority: str
    composite_severity: float
    composite_confidence: float
    state_name: str
    ida_name: str
    sanction_amount: float
    # 5 Core Governance Answers
    q1_what_happened: str
    q2_why_unusual: str
    q3_compared_with_what: str
    q4_supporting_evidence: Dict[str, Any]
    q5_limitations: str
    # Action Checklist
    next_review_actions: List[str]
    constituent_findings: List[Dict[str, Any]]

    @property
    def findings(self) -> List[Dict[str, Any]]:
        """Backwards compatibility alias for constituent_findings."""
        return self.constituent_findings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_id": self.work_id,
            "work_rec_id": self.work_rec_id,
            "priority": self.priority,
            "composite_severity": self.composite_severity,
            "composite_confidence": self.composite_confidence,
            "state_name": self.state_name,
            "ida_name": self.ida_name,
            "sanction_amount": self.sanction_amount,
            "five_questions": {
                "what_happened": self.q1_what_happened,
                "why_unusual": self.q2_why_unusual,
                "compared_with_what": self.q3_compared_with_what,
                "supporting_evidence": self.q4_supporting_evidence,
                "limitations": self.q5_limitations,
            },
            "next_review_actions": self.next_review_actions,
            "findings": self.constituent_findings,
        }

    def to_html(self, output_path: Any = None) -> str:
        """Renders self-contained interactive HTML dossier."""
        from src.engine.reporting.html_report import generate_dossier_html

        content = generate_dossier_html(self)
        if output_path:
            from pathlib import Path

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        return content


class DossierBuilder:
    """Constructs comprehensive explainable dossiers from scored work entities."""

    @staticmethod
    def build_dossier(work_score: WorkRiskScore) -> GovernanceDossier:
        findings = work_score.findings
        if not findings:
            return GovernanceDossier(
                work_id=work_score.work_id,
                work_rec_id=work_score.work_rec_id,
                priority=work_score.priority.value,
                composite_severity=work_score.composite_severity,
                composite_confidence=work_score.composite_confidence,
                state_name=work_score.state_name or "Unknown",
                ida_name=work_score.ida_name or "Unknown",
                sanction_amount=work_score.sanction_amount,
                q1_what_happened="No anomalies detected; work lifecycle aligns with statutory and statistical norms.",
                q2_why_unusual="N/A",
                q3_compared_with_what="MPLADS 2023 Guidelines and district peer cohorts.",
                q4_supporting_evidence={},
                q5_limitations="Data coverage is limited to public e-SAKSHI dashboard milestones.",
                next_review_actions=["Routine periodic progress monitoring."],
                constituent_findings=[],
            )

        # Question 1: What happened?
        what_happened = "; ".join([f.explanation for f in findings])

        # Question 2: Why is it unusual?
        reasons = []
        for f in findings:
            if f.category.value == "COMPLIANCE":
                reasons.append(f"Breaches legal operational rule ({f.detector_name})")
            elif f.category.value == "FINANCIAL":
                reasons.append(f"Statistically diverges from peer expenditure pattern ({f.detector_name})")
            elif f.category.value == "EXECUTION":
                reasons.append(f"Severe delivery delay or milestone mismatch ({f.detector_name})")
            elif f.category.value == "AGENCY":
                reasons.append(f"Concentration/capacity risk tied to agency ({f.detector_name})")
            else:
                reasons.append(f.detector_name)
        why_unusual = "; ".join(reasons)

        # Question 3: Compared with what?
        comparisons = []
        for f in findings:
            if "peer_cohort" in f.evidence:
                comparisons.append(f"Peer cohort: {f.evidence['peer_cohort']}")
            elif "statutory_limit_days" in f.evidence:
                comparisons.append(
                    f"Statutory limit: {f.evidence['statutory_limit_days']} days (MPLADS Guidelines 2023)"
                )
            elif "district_hhi" in f.evidence:
                comparisons.append("DOJ HHI concentration ceiling (2,500)")
            else:
                comparisons.append("Normalized historical district baseline")
        compared_with_what = "; ".join(list(set(comparisons)))

        # Question 4: Evidence
        evidence = {f.detector_code: f.evidence for f in findings}

        # Question 5: Limitations
        limitations = (
            f"Assessment based on unauthenticated e-SAKSHI pre-login REST datasets. Confidence score is "
            f"{work_score.composite_confidence:.1%}. Does not establish intentional wrongdoing or fraud."
        )

        # Action Checklist
        actions = [f.next_review_action for f in findings if f.next_review_action]

        return GovernanceDossier(
            work_id=work_score.work_id,
            work_rec_id=work_score.work_rec_id,
            priority=work_score.priority.value,
            composite_severity=work_score.composite_severity,
            composite_confidence=work_score.composite_confidence,
            state_name=work_score.state_name or "Unknown",
            ida_name=work_score.ida_name or "Unknown",
            sanction_amount=work_score.sanction_amount,
            q1_what_happened=what_happened,
            q2_why_unusual=why_unusual,
            q3_compared_with_what=compared_with_what,
            q4_supporting_evidence=evidence,
            q5_limitations=limitations,
            next_review_actions=actions,
            constituent_findings=[f.to_dict() for f in findings],
        )
