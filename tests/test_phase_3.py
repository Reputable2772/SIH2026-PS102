"""
Test Suite for Phase 3: Risk, Explainability & Validation Suite.
"""

import pytest
import pandas as pd
import numpy as np
from src.engine.detectors.base import Finding, AnomalyCategory
from src.engine.risk.composite_scorer import CompositeRiskScorer, ReviewPriority
from src.engine.risk.dossier import DossierBuilder
from src.validation.injection import AnomalyInjectionTester
from src.validation.benchmark import HistoricalAuditBenchmark
from src.validation.coverage_bias import CoverageBiasAuditor


def test_composite_risk_scorer_two_axis():
    df_works = pd.DataFrame([
        {
            "WORK_RECOMMENDATION_DTL_ID": "701",
            "WORK_ID": "W701",
            "STATE_NAME": "ODISHA",
            "IDA_NAME": "PURI",
            "SANCTION_AMOUNT": 1000000.0,
            "dqi_score": 0.90
        }
    ])

    findings = [
        Finding(
            finding_id="F1",
            work_id="W701",
            work_rec_id="701",
            detector_code="COMP-D1",
            detector_name="Sanction Turnaround SLA Breach",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.80,
            confidence=0.90,
            evidence={"overage_days": 60},
            explanation="Turnaround exceeded 45d SLA by 60 days.",
            next_review_action="Issue inquiry to IDA."
        ),
        Finding(
            finding_id="F2",
            work_id="W701",
            work_rec_id="701",
            detector_code="FIN-D6",
            detector_name="Sanction Cost Overrun",
            category=AnomalyCategory.FINANCIAL,
            severity=0.70,
            confidence=0.85,
            evidence={"overrun_ratio": 1.25},
            explanation="Disbursements exceeded sanction by 25%.",
            next_review_action="Demand revised sanction."
        )
    ]

    scorer = CompositeRiskScorer()
    scores = scorer.score_works(df_works, findings)

    assert len(scores) == 1
    s = scores[0]
    assert s.composite_severity >= 0.70
    assert s.composite_confidence >= 0.80
    assert s.has_statutory_breach == True
    assert s.priority == ReviewPriority.CRITICAL  # Elevated via statutory compliance breach


def test_dossier_builder_five_questions():
    df_works = pd.DataFrame([
        {
            "WORK_RECOMMENDATION_DTL_ID": "801",
            "WORK_ID": "W801",
            "STATE_NAME": "ASSAM",
            "IDA_NAME": "GUWAHATI",
            "SANCTION_AMOUNT": 750000.0,
            "dqi_score": 0.92
        }
    ])

    finding = Finding(
        finding_id="F801",
        work_id="W801",
        work_rec_id="801",
        detector_code="COMP-D2",
        detector_name="Execution Deadline SLA Breach",
        category=AnomalyCategory.COMPLIANCE,
        severity=0.75,
        confidence=0.88,
        evidence={"duration_days": 450, "statutory_limit_days": 365},
        explanation="Work exceeded 365-day execution deadline by 85 days.",
        next_review_action="Direct IA to submit physical progress report."
    )

    scorer = CompositeRiskScorer()
    scores = scorer.score_works(df_works, [finding])
    dossier = DossierBuilder.build_dossier(scores[0])

    assert dossier.q1_what_happened != ""
    assert dossier.q2_why_unusual != ""
    assert dossier.q3_compared_with_what != ""
    assert "COMP-D2" in dossier.q4_supporting_evidence
    assert "Confidence score" in dossier.q5_limitations
    assert len(dossier.next_review_actions) == 1
    assert "Direct IA" in dossier.next_review_actions[0]


def test_anomaly_injection_monotonicity():
    result = AnomalyInjectionTester.test_monotonicity()
    assert result["status"] == "PASS"
    assert result["is_monotonic"] == True


def test_anomaly_injection_cost_sensitivity():
    result = AnomalyInjectionTester.test_cost_sensitivity()
    assert result["status"] == "PASS"
    assert result["has_fin_d5_finding"] == True
    assert result["is_elevated"] == True


def test_historical_audit_benchmark_recall():
    result = HistoricalAuditBenchmark.evaluate_benchmark()
    assert result["status"] == "PASS"
    assert result["recall_pct"] >= 90.0
    assert result["true_positives"] >= 15
    assert "Flagged" in result["summary"]


def test_coverage_bias_auditor():
    df = pd.DataFrame([
        {"WORK_RECOMMENDATION_DTL_ID": f"B-{i}", "STATE_NAME": f"STATE_{i%8}", "dqi_score": 0.70 + (i%5)*0.05}
        for i in range(120)
    ])
    findings = [
        Finding(
            finding_id=f"FB-{i}", work_id=f"B-{i*3}", work_rec_id=f"B-{i*3}",
            detector_code="COMP-D1", detector_name="", category=AnomalyCategory.COMPLIANCE,
            severity=0.5, confidence=0.8, evidence={}, explanation="", next_review_action=""
        )
        for i in range(20)
    ]

    bias = CoverageBiasAuditor.audit_coverage_bias(df, findings)
    assert "spearman_rho" in bias
    assert bias["status"] in {"PASS", "WARNING"}
