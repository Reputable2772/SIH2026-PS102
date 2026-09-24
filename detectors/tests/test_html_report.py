"""
Tests for self-contained interactive HTML reporting.
"""

import pandas as pd

from src.engine.coordinator import DetectionResultSet
from src.engine.detectors.base import AnomalyCategory, AnomalyFinding
from src.engine.reporting.html_report import generate_audit_report_html, generate_dossier_html
from src.engine.risk.composite_scorer import ReviewPriority, WorkRiskScore
from src.engine.risk.dossier import GovernanceDossier


def test_dossier_html_rendering_elements():
    """Ensures that all 5 governance questions, metadata, and actions are rendered."""
    dossier = GovernanceDossier(
        work_id="W100",
        work_rec_id="REC100",
        priority="CRITICAL",
        composite_severity=0.88,
        composite_confidence=0.92,
        state_name="ASSAM",
        ida_name="KAMRUP",
        sanction_amount=2500000.0,
        q1_what_happened="Sanction SLA breached by 120 days.",
        q2_why_unusual="Exceeds 45-day statutory limit in MPLADS Guidelines.",
        q3_compared_with_what="Statutory limit: 45 days",
        q4_supporting_evidence={"delay_days": 165},
        q5_limitations="e-SAKSHI pre-login milestone limitations.",
        next_review_actions=["Issue notice to District Authority for sanction delay explanation."],
        constituent_findings=[],
    )

    rendered = generate_dossier_html(dossier)

    assert "<!DOCTYPE html>" in rendered
    assert "REC100" in rendered
    assert "CRITICAL" in rendered
    assert "Sanction SLA breached by 120 days" in rendered
    assert "Q1: What Happened?" in rendered
    assert "Q2: Why Is It Unusual?" in rendered
    assert "Q3: Compared With What?" in rendered
    assert "Q4: Supporting Evidence & Telemetry" in rendered
    assert "Q5: Known Data Limitations" in rendered
    assert "Issue notice to District Authority" in rendered
    assert "Print / Export PDF" in rendered


def test_audit_report_html_table_and_kpis():
    """Ensures that the comprehensive audit report includes search, filters, and KPI cards."""
    score1 = WorkRiskScore(
        work_id="W1",
        work_rec_id="R1",
        composite_severity=0.9,
        composite_confidence=0.85,
        priority=ReviewPriority.CRITICAL,
        findings_count=1,
        category_severities={"COMPLIANCE": 0.9},
        has_statutory_breach=True,
        state_name="KERALA",
        ida_name="WAYANAD",
        sanction_amount=1000000.0,
        findings=[
            AnomalyFinding(
                work_id="W1",
                detector_code="COMP-D1",
                detector_name="Sanction SLA Exceeded",
                category=AnomalyCategory.COMPLIANCE,
                severity=0.9,
                confidence=0.85,
                evidence={"delay": 60},
                explanation="Exceeded sanction timeline.",
                next_review_action="Audit sanction logs.",
                work_rec_id="R1",
            )
        ],
    )

    results = DetectionResultSet(
        works=pd.DataFrame([{"WORK_RECOMMENDATION_DTL_ID": "R1"}]), scores=[score1], findings=score1.findings
    )

    html_out = generate_audit_report_html(results, title="Kerala Audit Report")

    assert "Kerala Audit Report" in html_out
    assert "Critical Attention" in html_out
    assert "Search by Work ID" in html_out
    assert "Audit sanction logs" in html_out
    assert 'data-priority="CRITICAL"' in html_out


def test_dossier_html_rendering_with_findings():
    """Verifies that triggered detector badges are correctly extracted and rendered."""
    dossier = GovernanceDossier(
        work_id="W200",
        work_rec_id="REC200",
        priority="CRITICAL",
        composite_severity=0.95,
        composite_confidence=0.88,
        state_name="BIHAR",
        ida_name="PATNA",
        sanction_amount=5000000.0,
        q1_what_happened="Multiple anomalies detected.",
        q2_why_unusual="Breaches legal operational rule and cost peer distribution.",
        q3_compared_with_what="Statutory SLA 45 days and district peer cohort.",
        q4_supporting_evidence={"COMP-D1": {"overage": 60}, "FIN-D5": {"z_score": 3.2}},
        q5_limitations="e-SAKSHI data limits.",
        next_review_actions=["Audit project files."],
        constituent_findings=[
            {"detector_code": "COMP-D1", "detector_name": "Sanction SLA Breach", "severity": 0.8},
            {"detector_code": "FIN-D5", "detector_name": "Cost Peer Outlier", "severity": 0.9},
        ],
    )

    rendered = generate_dossier_html(dossier)

    # Must render both detector badges
    assert "COMP-D1" in rendered
    assert "FIN-D5" in rendered
    assert '<span class="badge badge-anomaly">COMP-D1</span>' in rendered
    assert '<span class="badge badge-anomaly">FIN-D5</span>' in rendered
    assert "None (Clean)" not in rendered
    # Must support .findings property alias
    assert len(dossier.findings) == 2
    assert dossier.findings[0]["detector_code"] == "COMP-D1"
