"""
Test Suite for Phase 3: Risk, Explainability & Validation Suite.
"""

import pandas as pd

from src.engine.detectors.base import AnomalyCategory, Finding
from src.engine.risk.composite_scorer import CompositeRiskScorer, ReviewPriority
from src.engine.risk.dossier import DossierBuilder
from src.validation.benchmark import HistoricalAuditBenchmark
from src.validation.coverage_bias import CoverageBiasAuditor
from src.validation.injection import AnomalyInjectionTester


def test_composite_risk_scorer_two_axis():
    df_works = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "701",
                "WORK_ID": "W701",
                "STATE_NAME": "ODISHA",
                "IDA_NAME": "PURI",
                "SANCTION_AMOUNT": 1000000.0,
                "dqi_score": 0.90,
            }
        ]
    )

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
            next_review_action="Issue inquiry to IDA.",
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
            next_review_action="Demand revised sanction.",
        ),
    ]

    scorer = CompositeRiskScorer()
    scores = scorer.score_works(df_works, findings)

    assert len(scores) == 1
    s = scores[0]
    assert s.composite_severity >= 0.70
    assert s.composite_confidence >= 0.80
    assert s.has_statutory_breach is True
    assert s.priority == ReviewPriority.CRITICAL  # Elevated via statutory compliance breach


def test_dossier_builder_five_questions():
    df_works = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "801",
                "WORK_ID": "W801",
                "STATE_NAME": "ASSAM",
                "IDA_NAME": "GUWAHATI",
                "SANCTION_AMOUNT": 750000.0,
                "dqi_score": 0.92,
            }
        ]
    )

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
        next_review_action="Direct IA to submit physical progress report.",
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
    assert result["is_monotonic"] is True


def test_anomaly_injection_cost_sensitivity():
    result = AnomalyInjectionTester.test_cost_sensitivity()
    assert result["status"] == "PASS"
    assert result["has_fin_d5_finding"] is True
    assert result["is_elevated"] is True


def test_historical_audit_benchmark_recall():
    result = HistoricalAuditBenchmark.evaluate_benchmark()
    assert result["status"] == "PASS"
    assert result["recall_pct"] >= 90.0
    assert result["true_positives"] >= 15
    assert "Flagged" in result["summary"]


def test_coverage_bias_auditor():
    df = pd.DataFrame(
        [
            {"WORK_RECOMMENDATION_DTL_ID": f"B-{i}", "STATE_NAME": f"STATE_{i % 8}", "dqi_score": 0.70 + (i % 5) * 0.05}
            for i in range(120)
        ]
    )
    findings = [
        Finding(
            finding_id=f"FB-{i}",
            work_id=f"B-{i * 3}",
            work_rec_id=f"B-{i * 3}",
            detector_code="COMP-D1",
            detector_name="",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.5,
            confidence=0.8,
            evidence={},
            explanation="",
            next_review_action="",
        )
        for i in range(20)
    ]

    bias = CoverageBiasAuditor.audit_coverage_bias(df, findings)
    assert "spearman_rho" in bias
    assert bias["status"] in {"PASS", "WARNING"}


def test_composite_scorer_multi_signal_monotonicity():
    """
    Verifies that adding anomaly findings across additional categories strictly non-decreases
    composite severity (preventing the active-weight averaging inversion defect).
    """
    df_work = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "MONO-1",
                "WORK_ID": "WMONO1",
                "STATE_NAME": "MAHARASHTRA",
                "IDA_NAME": "NASHIK",
                "SANCTION_AMOUNT": 500000.0,
                "dqi_score": 0.90,
            }
        ]
    )

    f_comp = Finding(
        finding_id="F1",
        work_id="WMONO1",
        work_rec_id="MONO-1",
        detector_code="COMP-D2",
        detector_name="",
        category=AnomalyCategory.COMPLIANCE,
        severity=0.60,
        confidence=0.8,
        evidence={},
        explanation="",
        next_review_action="",
    )
    f_fin = Finding(
        finding_id="F2",
        work_id="WMONO1",
        work_rec_id="MONO-1",
        detector_code="FIN-D5",
        detector_name="",
        category=AnomalyCategory.FINANCIAL,
        severity=0.50,
        confidence=0.8,
        evidence={},
        explanation="",
        next_review_action="",
    )
    f_exec = Finding(
        finding_id="F3",
        work_id="WMONO1",
        work_rec_id="MONO-1",
        detector_code="EXEC-D9",
        detector_name="",
        category=AnomalyCategory.EXECUTION,
        severity=0.40,
        confidence=0.8,
        evidence={},
        explanation="",
        next_review_action="",
    )

    scorer = CompositeRiskScorer()
    s1 = scorer.score_works(df_work, [f_comp])[0]
    s2 = scorer.score_works(df_work, [f_comp, f_fin])[0]
    s3 = scorer.score_works(df_work, [f_comp, f_fin, f_exec])[0]

    assert s1.composite_severity < s2.composite_severity, (
        f"Adding a second category must increase composite severity: s1={s1.composite_severity}, s2={s2.composite_severity}"
    )
    assert s2.composite_severity < s3.composite_severity, (
        f"Adding a third category must increase composite severity: s2={s2.composite_severity}, s3={s3.composite_severity}"
    )


def test_composite_scorer_isolated_d1_capped():
    """
    Verifies that an isolated administrative sanction delay (COMP-D1) cannot reach 1.0 composite
    severity or displace physical/financial disasters to CRITICAL review priority.
    """
    from src.engine.detectors.compliance import SanctionSLABreachDetector

    det = SanctionSLABreachDetector()
    work_df = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "D1_ONLY",
                "WORK_ID": "WD1",
                "days_rec_to_sanction": 400,  # 355 days overage (> 1 year delay)
                "RECOMMENDATION_DATE": "2024-01-01",
                "SANCTION_DATE": "2025-02-04",
                "dqi_score": 0.90,
                "STATE_NAME": "PUNJAB",
                "IDA_NAME": "AMRITSAR",
                "SANCTION_AMOUNT": 500000.0,
            }
        ]
    )

    findings = det.detect(work_df)
    assert len(findings) == 1
    assert findings[0].severity <= 0.60, f"D1 severity must be capped <= 0.60, got {findings[0].severity}"

    scorer = CompositeRiskScorer()
    scores = scorer.score_works(work_df, findings)
    s = scores[0]

    assert s.composite_severity < 0.60
    assert s.priority != ReviewPriority.CRITICAL, "Single administrative delay must not be ranked CRITICAL"


def test_scoring_property_duplicate_subadditivity():
    """
    Verifies that multiple findings within the same category are subadditive
    (take max category severity rather than summing unboundedly).
    """
    df_work = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "SUB_1",
                "WORK_ID": "WSUB1",
                "STATE_NAME": "KERALA",
                "IDA_NAME": "WAYANAD",
                "SANCTION_AMOUNT": 500000.0,
                "dqi_score": 0.90,
            }
        ]
    )

    f1 = Finding(
        finding_id="F1",
        work_id="WSUB1",
        work_rec_id="SUB_1",
        detector_code="COMP-D1",
        detector_name="",
        category=AnomalyCategory.COMPLIANCE,
        severity=0.50,
        confidence=0.8,
        evidence={},
        explanation="",
        next_review_action="",
    )
    f2 = Finding(
        finding_id="F2",
        work_id="WSUB1",
        work_rec_id="SUB_1",
        detector_code="COMP-D2",
        detector_name="",
        category=AnomalyCategory.COMPLIANCE,
        severity=0.70,
        confidence=0.8,
        evidence={},
        explanation="",
        next_review_action="",
    )

    scorer = CompositeRiskScorer()
    s_single = scorer.score_works(df_work, [f2])[0]
    s_dual_same_cat = scorer.score_works(df_work, [f1, f2])[0]

    # Category severity for COMPLIANCE must be max(0.50, 0.70) = 0.70
    assert s_dual_same_cat.category_severities[AnomalyCategory.COMPLIANCE.value] == 0.70
    # Composite severity must not sum 0.50 + 0.70 to 1.20
    assert s_dual_same_cat.composite_severity <= 0.85
    assert s_dual_same_cat.composite_severity == s_single.composite_severity, (
        "Findings in the same category must take the category max without duplicate inflation"
    )


def test_scoring_property_confidence_severity_separation():
    """
    Verifies that data completeness (DQI) influences composite confidence,
    while leaving composite severity strictly invariant (orthogonality invariant).
    """
    df_high_dqi = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "ORTHO_1",
                "WORK_ID": "WORTHO1",
                "STATE_NAME": "GUJARAT",
                "IDA_NAME": "SURAT",
                "SANCTION_AMOUNT": 500000.0,
                "dqi_score": 0.95,
            }
        ]
    )
    df_low_dqi = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "ORTHO_1",
                "WORK_ID": "WORTHO1",
                "STATE_NAME": "GUJARAT",
                "IDA_NAME": "SURAT",
                "SANCTION_AMOUNT": 500000.0,
                "dqi_score": 0.35,
            }
        ]
    )

    f = Finding(
        finding_id="F1",
        work_id="WORTHO1",
        work_rec_id="ORTHO_1",
        detector_code="FIN-D5",
        detector_name="",
        category=AnomalyCategory.FINANCIAL,
        severity=0.75,
        confidence=0.85,
        evidence={},
        explanation="",
        next_review_action="",
    )

    scorer = CompositeRiskScorer()
    s_high = scorer.score_works(df_high_dqi, [f])[0]
    s_low = scorer.score_works(df_low_dqi, [f])[0]

    # Severities must be exactly identical
    assert abs(s_high.composite_severity - s_low.composite_severity) < 1e-6
    # Confidences must differ substantially reflecting source data completeness
    assert s_high.composite_confidence > s_low.composite_confidence
    assert s_high.composite_confidence >= 0.85
    assert s_low.composite_confidence <= 0.55


def test_scoring_property_statutory_override_distinguishable():
    """
    Verifies that statutory overrides are explicitly distinguishable via
    has_statutory_breach field, enabling reviewers to audit legal breaches distinctly.
    """
    df_work = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "STAT_1",
                "WORK_ID": "WSTAT1",
                "STATE_NAME": "BIHAR",
                "IDA_NAME": "PATNA",
                "SANCTION_AMOUNT": 500000.0,
                "dqi_score": 0.90,
            }
        ]
    )

    # Statutory breach finding: COMP-D2 prolonged execution SLA breach
    f_stat = Finding(
        finding_id="FS",
        work_id="WSTAT1",
        work_rec_id="STAT_1",
        detector_code="COMP-D2",
        detector_name="",
        category=AnomalyCategory.COMPLIANCE,
        severity=0.80,
        confidence=0.90,
        evidence={},
        explanation="",
        next_review_action="",
    )
    # Non-statutory statistical outlier: FIN-D5 cost peer outlier
    f_nonstat = Finding(
        finding_id="FNS",
        work_id="WSTAT1",
        work_rec_id="STAT_1",
        detector_code="FIN-D5",
        detector_name="",
        category=AnomalyCategory.FINANCIAL,
        severity=0.80,
        confidence=0.90,
        evidence={},
        explanation="",
        next_review_action="",
    )

    scorer = CompositeRiskScorer()
    s_stat = scorer.score_works(df_work, [f_stat])[0]
    s_nonstat = scorer.score_works(df_work, [f_nonstat])[0]

    assert s_stat.has_statutory_breach is True
    assert s_nonstat.has_statutory_breach is False
    assert s_stat.priority == ReviewPriority.CRITICAL  # Elevated via statutory compliance breach
