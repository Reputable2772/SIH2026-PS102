"""
Test Suite for Phase 2: Cross-Work, Entity & Pattern Intelligence.
"""

import numpy as np
import pandas as pd

from src.engine.cross_work import CrossWorkIntelligenceEngine
from src.engine.cross_work.concentration import AgencyConcentrationDetector, VendorConcentrationDetector
from src.engine.cross_work.recurrence import EntityRecurrenceDetector
from src.engine.cross_work.similarity import DuplicateWorkDetector
from src.engine.cross_work.trends import TrendAnalyzer
from src.engine.detectors.base import AnomalyCategory, Finding


def test_duplicate_work_detector():
    df = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "201",
                "WORK_ID": "W201",
                "STATE_NAME": "PUNJAB",
                "IDA_NAME": "AMRITSAR",
                "WORK_CATEGORY": "Community Halls",
                "WORK_DESCRIPTION": "Construction of modern community hall near Gurudwara Sahib block A",
                "SANCTION_AMOUNT": 1500000.0,
                "dqi_score": 0.90,
            },
            {
                "WORK_RECOMMENDATION_DTL_ID": "202",
                "WORK_ID": "W202",
                "STATE_NAME": "PUNJAB",
                "IDA_NAME": "AMRITSAR",
                "WORK_CATEGORY": "Community Halls",
                "WORK_DESCRIPTION": "Construction of modern community hall near Gurudwara Sahib block A with veranda",
                "SANCTION_AMOUNT": 1520000.0,
                "dqi_score": 0.90,
            },
            {
                "WORK_RECOMMENDATION_DTL_ID": "203",
                "WORK_ID": "W203",
                "STATE_NAME": "PUNJAB",
                "IDA_NAME": "AMRITSAR",
                "WORK_CATEGORY": "Community Halls",
                "WORK_DESCRIPTION": "Laying of underground sewerage pipe network at sector 4",
                "SANCTION_AMOUNT": 800000.0,
                "dqi_score": 0.90,
            },
        ]
    )

    detector = DuplicateWorkDetector(similarity_threshold=0.75, cost_window_ratio=0.20)
    findings = detector.detect(df)

    assert len(findings) >= 1
    f = findings[0]
    assert f.detector_code == "SIM-D12"
    assert "202" in f.evidence["matched_work_rec_id"] or "201" in f.evidence["matched_work_rec_id"]
    assert f.evidence["same_district"] is True
    assert len(f.next_review_action) > 0


def test_agency_concentration_detector():
    records = []
    # 20 works in district, 16 assigned to same IA (80% share)
    for i in range(20):
        ia = "DOMINANT_PWD" if i < 16 else "OTHER_AGENCY"
        records.append(
            {
                "WORK_RECOMMENDATION_DTL_ID": f"30{i}",
                "WORK_ID": f"W30{i}",
                "STATE_NAME": "HARYANA",
                "IDA_NAME": "GURGAON",
                "ia_name": ia,
                "SANCTION_AMOUNT": 500000.0,
            }
        )
    df = pd.DataFrame(records)

    detector = AgencyConcentrationDetector(hhi_threshold=2500, share_threshold=0.40)
    findings = detector.detect(df)

    assert len(findings) > 0
    f = findings[0]
    assert f.detector_code == "AGY-D13"
    assert f.evidence["dominant_ia"] == "DOMINANT_PWD"
    assert f.evidence["agency_share_pct"] == 80.0
    assert f.evidence["district_hhi"] > 6000


def test_vendor_concentration_detector():
    records = []
    # District with 15 works, Vendor MONOPOLY gets 10 works with 80% disbursement
    for i in range(15):
        vendor = "MONOPOLY_CONSTRUCTION" if i < 10 else f"VENDOR_{i}"
        disb = 200000.0 if i < 10 else 25000.0
        records.append(
            {
                "WORK_RECOMMENDATION_DTL_ID": f"40{i}",
                "WORK_ID": f"W40{i}",
                "STATE_NAME": "RAJASTHAN",
                "IDA_NAME": "JAIPUR",
                "primary_vendor": vendor, "primary_vendor_id": f"VID_{vendor}",
                "total_disbursed": disb,
                "SANCTION_AMOUNT": disb,
            }
        )
    df = pd.DataFrame(records)

    detector = VendorConcentrationDetector(share_threshold=0.50, min_vendor_works=5)
    findings = detector.detect(df)

    assert len(findings) > 0
    f = findings[0]
    assert f.detector_code == "VND-D14"
    assert f.evidence["vendor_name"] == "MONOPOLY_CONSTRUCTION"
    assert f.evidence["vendor_share_pct"] > 50.0


def test_vendor_concentration_gating_behavior():
    """
    Section 5 Audit Regression Test:
    Proves that CrossWorkIntelligenceEngine gates VND-D14 by default (Core.md FR-08 / AC-07),
    and only runs vendor concentration when explicitly un-gated.
    """
    records = []
    for i in range(15):
        records.append(
            {
                "WORK_RECOMMENDATION_DTL_ID": f"V40{i}",
                "WORK_ID": f"WV40{i}",
                "STATE_NAME": "RAJASTHAN",
                "IDA_NAME": "JAIPUR",
                "primary_vendor": "MONOPOLY_CONSTRUCTION" if i < 10 else f"VENDOR_{i}",
                "primary_vendor_id": "V_MONOPOLY" if i < 10 else f"V_{i}",
                "ia_name": "RURAL_DEV",
                "total_disbursed": 200000.0 if i < 10 else 25000.0,
                "SANCTION_AMOUNT": 200000.0 if i < 10 else 25000.0,
                "WORK_CATEGORY": "Roads",
                "WORK_DESCRIPTION": f"Construction of road segment {i} in Jaipur",
            }
        )
    df = pd.DataFrame(records)

    # 1. Default engine: GATED (0 VND-D14 findings)
    gated_engine = CrossWorkIntelligenceEngine(enable_vendor_concentration=False)
    gated_findings = gated_engine.run(df)
    vnd_codes = [f.detector_code for f in gated_findings if f.detector_code == "VND-D14"]
    assert len(vnd_codes) == 0, "VND-D14 should be strictly gated by default"

    # 2. Explicitly enabled engine: ACTIVE (>0 VND-D14 findings)
    active_engine = CrossWorkIntelligenceEngine(enable_vendor_concentration=True)
    active_findings = active_engine.run(df)
    active_vnd = [f.detector_code for f in active_findings if f.detector_code == "VND-D14"]
    assert len(active_vnd) > 0, "VND-D14 should produce findings when explicitly enabled"


def test_entity_recurrence_detector():
    works = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "501",
                "ia_name": "REPEAT_IA",
                "STATE_NAME": "BIHAR",
                "IDA_NAME": "PATNA",
                "SANCTION_AMOUNT": 500000.0,
            },
            {
                "WORK_RECOMMENDATION_DTL_ID": "502",
                "ia_name": "REPEAT_IA",
                "STATE_NAME": "BIHAR",
                "IDA_NAME": "PATNA",
                "SANCTION_AMOUNT": 500000.0,
            },
            {
                "WORK_RECOMMENDATION_DTL_ID": "503",
                "ia_name": "REPEAT_IA",
                "STATE_NAME": "BIHAR",
                "IDA_NAME": "PATNA",
                "SANCTION_AMOUNT": 500000.0,
            },
        ]
    )

    # Prior findings across all 3 works
    prior = [
        Finding(
            finding_id="F1",
            work_id="501",
            work_rec_id="501",
            detector_code="COMP-D1",
            detector_name="Turnaround",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.7,
            confidence=0.8,
            evidence={},
            explanation="",
            next_review_action="",
        ),
        Finding(
            finding_id="F2",
            work_id="502",
            work_rec_id="502",
            detector_code="FIN-D5",
            detector_name="Cost",
            category=AnomalyCategory.FINANCIAL,
            severity=0.8,
            confidence=0.8,
            evidence={},
            explanation="",
            next_review_action="",
        ),
        Finding(
            finding_id="F3",
            work_id="503",
            work_rec_id="503",
            detector_code="COMP-D2",
            detector_name="Delay",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.75,
            confidence=0.8,
            evidence={},
            explanation="",
            next_review_action="",
        ),
    ]

    detector = EntityRecurrenceDetector(min_anomalies=3)
    findings = detector.detect(works, prior)

    assert len(findings) == 3
    assert all(f.detector_code == "REC-D15" for f in findings)
    assert all(f.evidence["entity_name"] == "REPEAT_IA" for f in findings)
    assert all(f.evidence["flagged_works_count"] == 3 for f in findings)
    assert {f.work_rec_id for f in findings} == {"501", "502", "503"}


def test_recurrence_tiny_portfolios_not_extreme():
    """Verifies that tiny portfolios (N < 3) never trigger REC-D15 even if 100% of works are anomalous."""
    works = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "T1",
                "ia_name": "TINY_IA",
                "STATE_NAME": "GOA",
                "IDA_NAME": "NORTH GOA",
                "SANCTION_AMOUNT": 100000.0,
            },
            {
                "WORK_RECOMMENDATION_DTL_ID": "T2",
                "ia_name": "TINY_IA",
                "STATE_NAME": "GOA",
                "IDA_NAME": "NORTH GOA",
                "SANCTION_AMOUNT": 100000.0,
            },
        ]
    )
    prior = [
        Finding(
            finding_id="FT1",
            work_id="T1",
            work_rec_id="T1",
            detector_code="COMP-D1",
            detector_name="",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.7,
            confidence=0.8,
            evidence={},
            explanation="",
            next_review_action="",
        ),
        Finding(
            finding_id="FT2",
            work_id="T2",
            work_rec_id="T2",
            detector_code="COMP-D2",
            detector_name="",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.8,
            confidence=0.8,
            evidence={},
            explanation="",
            next_review_action="",
        ),
    ]
    det = EntityRecurrenceDetector(min_anomalies=3, min_exposure=3)
    findings = det.detect(works, prior)
    assert len(findings) == 0, "Tiny portfolio with N=2 must not trigger REC-D15"


def test_recurrence_large_portfolios_not_penalized_for_volume():
    """
    Verifies that a large portfolio agency with a low/baseline anomaly rate is NOT flagged,
    while a large portfolio agency with a high anomaly rate IS flagged.
    """
    works = []
    prior = []
    # Agency GOOD_LARGE: N=50 works, only 5 anomalous (10% failure rate)
    for i in range(50):
        rid = f"GL_{i}"
        works.append(
            {
                "WORK_RECOMMENDATION_DTL_ID": rid,
                "ia_name": "GOOD_LARGE_IA",
                "STATE_NAME": "UP",
                "IDA_NAME": "AGRA",
                "SANCTION_AMOUNT": 200000.0,
            }
        )
        if i < 5:
            prior.append(
                Finding(
                    finding_id=f"F_GL_{i}",
                    work_id=rid,
                    work_rec_id=rid,
                    detector_code="COMP-D1",
                    detector_name="",
                    category=AnomalyCategory.COMPLIANCE,
                    severity=0.5,
                    confidence=0.8,
                    evidence={},
                    explanation="",
                    next_review_action="",
                )
            )

    # Agency BAD_LARGE: N=50 works, 40 anomalous (80% failure rate)
    for i in range(50):
        rid = f"BL_{i}"
        works.append(
            {
                "WORK_RECOMMENDATION_DTL_ID": rid,
                "ia_name": "BAD_LARGE_IA",
                "STATE_NAME": "UP",
                "IDA_NAME": "AGRA",
                "SANCTION_AMOUNT": 200000.0,
            }
        )
        if i < 40:
            prior.append(
                Finding(
                    finding_id=f"F_BL_{i}",
                    work_id=rid,
                    work_rec_id=rid,
                    detector_code="COMP-D1",
                    detector_name="",
                    category=AnomalyCategory.COMPLIANCE,
                    severity=0.5,
                    confidence=0.8,
                    evidence={},
                    explanation="",
                    next_review_action="",
                )
            )

    # Background peer agencies to establish peer baseline ~ 40%
    for a in range(10):
        for w in range(10):
            rid = f"BG_{a}_{w}"
            works.append(
                {
                    "WORK_RECOMMENDATION_DTL_ID": rid,
                    "ia_name": f"PEER_IA_{a}",
                    "STATE_NAME": "UP",
                    "IDA_NAME": "AGRA",
                    "SANCTION_AMOUNT": 200000.0,
                }
            )
            if w < 4:
                prior.append(
                    Finding(
                        finding_id=f"F_BG_{a}_{w}",
                        work_id=rid,
                        work_rec_id=rid,
                        detector_code="COMP-D1",
                        detector_name="",
                        category=AnomalyCategory.COMPLIANCE,
                        severity=0.5,
                        confidence=0.8,
                        evidence={},
                        explanation="",
                        next_review_action="",
                    )
                )

    df_works = pd.DataFrame(works)
    det = EntityRecurrenceDetector(min_anomalies=3, min_exposure=3)
    findings = det.detect(df_works, prior)

    flagged_entities = {f.evidence["entity_name"] for f in findings}
    assert "GOOD_LARGE_IA" not in flagged_entities, (
        "Large agency with low anomaly rate (10%) must NOT be penalized for volume"
    )
    assert "BAD_LARGE_IA" in flagged_entities, "Large agency with high anomaly rate (80%) MUST be flagged"


def test_recurrence_missing_exposure_distinction():
    """Verifies that missing or null IA names are ignored and never grouped as a valid entity."""
    works = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "M1",
                "ia_name": None,
                "STATE_NAME": "BIHAR",
                "IDA_NAME": "GAYA",
                "SANCTION_AMOUNT": 100000.0,
            },
            {
                "WORK_RECOMMENDATION_DTL_ID": "M2",
                "ia_name": np.nan,
                "STATE_NAME": "BIHAR",
                "IDA_NAME": "GAYA",
                "SANCTION_AMOUNT": 100000.0,
            },
            {
                "WORK_RECOMMENDATION_DTL_ID": "M3",
                "ia_name": "",
                "STATE_NAME": "BIHAR",
                "IDA_NAME": "GAYA",
                "SANCTION_AMOUNT": 100000.0,
            },
        ]
    )
    prior = [
        Finding(
            finding_id="FM1",
            work_id="M1",
            work_rec_id="M1",
            detector_code="COMP-D1",
            detector_name="",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.5,
            confidence=0.8,
            evidence={},
            explanation="",
            next_review_action="",
        ),
        Finding(
            finding_id="FM2",
            work_id="M2",
            work_rec_id="M2",
            detector_code="COMP-D1",
            detector_name="",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.5,
            confidence=0.8,
            evidence={},
            explanation="",
            next_review_action="",
        ),
        Finding(
            finding_id="FM3",
            work_id="M3",
            work_rec_id="M3",
            detector_code="COMP-D1",
            detector_name="",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.5,
            confidence=0.8,
            evidence={},
            explanation="",
            next_review_action="",
        ),
    ]
    det = EntityRecurrenceDetector(min_anomalies=3, min_exposure=3)
    findings = det.detect(works, prior)
    assert len(findings) == 0, "Null, NaN, and empty IA names must not trigger recurrence findings"


def test_recurrence_deterministic_and_reproducible():
    """Verifies that running detection repeatedly on the same data produces identical results."""
    works = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": f"D_{i}",
                "ia_name": "STABLE_IA",
                "STATE_NAME": "KERALA",
                "IDA_NAME": "KOCHI",
                "SANCTION_AMOUNT": 300000.0,
            }
            for i in range(10)
        ]
    )
    prior = [
        Finding(
            finding_id=f"FD_{i}",
            work_id=f"D_{i}",
            work_rec_id=f"D_{i}",
            detector_code="FIN-D5",
            detector_name="",
            category=AnomalyCategory.FINANCIAL,
            severity=0.8,
            confidence=0.9,
            evidence={},
            explanation="",
            next_review_action="",
        )
        for i in range(8)
    ]
    det = EntityRecurrenceDetector(min_anomalies=3, min_exposure=3)
    f1 = det.detect(works, prior)
    f2 = det.detect(works, prior)

    assert len(f1) == len(f2) == 8
    assert f1[0].evidence["z_score"] == f2[0].evidence["z_score"]
    assert f1[0].evidence["p_value"] == f2[0].evidence["p_value"]
    assert f1[0].severity == f2[0].severity
    assert f1[0].confidence == f2[0].confidence


def test_recurrence_explainability_fields_integrity():
    """Verifies all mandatory explainability fields are present and well-formed."""
    works = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": f"E_{i}",
                "ia_name": "EXPLAIN_IA",
                "STATE_NAME": "ASSAM",
                "IDA_NAME": "JORHAT",
                "SANCTION_AMOUNT": 400000.0,
            }
            for i in range(10)
        ]
    )
    prior = [
        Finding(
            finding_id=f"FE_{i}",
            work_id=f"E_{i}",
            work_rec_id=f"E_{i}",
            detector_code="COMP-D2",
            detector_name="",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.75,
            confidence=0.85,
            evidence={},
            explanation="",
            next_review_action="",
        )
        for i in range(9)
    ]
    det = EntityRecurrenceDetector(min_anomalies=3, min_exposure=3)
    findings = det.detect(works, prior)

    assert len(findings) == 9
    f = findings[0]
    ev = f.evidence
    for k in [
        "entity_type",
        "entity_name",
        "flagged_works_count",
        "total_portfolio_works",
        "raw_failure_rate",
        "shrunk_failure_rate",
        "peer_baseline_rate",
        "z_score",
        "p_value",
        "contributing_anomaly_types",
    ]:
        assert k in ev, f"Missing evidence key: {k}"
    assert ev["flagged_works_count"] == 9
    assert ev["total_portfolio_works"] == 10
    assert ev["raw_failure_rate"] == 0.9
    assert len(f.explanation) > 20
    assert len(f.next_review_action) > 20


def test_recurrence_severity_and_confidence_distinct():
    """
    Verifies that Severity (excess rate above baseline) and Confidence (sample size & certainty)
    remain distinct orthogonal concepts.
    """
    # Cohort 1: Small exposure (N=4, k=4, 100% fail) -> High excess, moderate confidence
    # Cohort 2: Large exposure (N=60, k=30, 50% fail vs ~30% peer) -> Moderate excess, very high confidence
    works = []
    prior = []
    for i in range(4):
        rid = f"SMALL_{i}"
        works.append(
            {
                "WORK_RECOMMENDATION_DTL_ID": rid,
                "ia_name": "SMALL_IA",
                "STATE_NAME": "DELHI",
                "IDA_NAME": "EAST",
                "SANCTION_AMOUNT": 100000.0,
            }
        )
        prior.append(
            Finding(
                finding_id=f"FS_{i}",
                work_id=rid,
                work_rec_id=rid,
                detector_code="COMP-D1",
                detector_name="",
                category=AnomalyCategory.COMPLIANCE,
                severity=0.6,
                confidence=0.8,
                evidence={},
                explanation="",
                next_review_action="",
            )
        )

    for i in range(60):
        rid = f"LARGE_{i}"
        works.append(
            {
                "WORK_RECOMMENDATION_DTL_ID": rid,
                "ia_name": "LARGE_IA",
                "STATE_NAME": "DELHI",
                "IDA_NAME": "EAST",
                "SANCTION_AMOUNT": 100000.0,
            }
        )
        if i < 30:
            prior.append(
                Finding(
                    finding_id=f"FL_{i}",
                    work_id=rid,
                    work_rec_id=rid,
                    detector_code="COMP-D1",
                    detector_name="",
                    category=AnomalyCategory.COMPLIANCE,
                    severity=0.6,
                    confidence=0.8,
                    evidence={},
                    explanation="",
                    next_review_action="",
                )
            )

    # Add background peers with 25% failure rate
    for a in range(15):
        for w in range(10):
            rid = f"BG_{a}_{w}"
            works.append(
                {
                    "WORK_RECOMMENDATION_DTL_ID": rid,
                    "ia_name": f"BG_{a}",
                    "STATE_NAME": "DELHI",
                    "IDA_NAME": "EAST",
                    "SANCTION_AMOUNT": 100000.0,
                }
            )
            if w < 2:
                prior.append(
                    Finding(
                        finding_id=f"FB_{a}_{w}",
                        work_id=rid,
                        work_rec_id=rid,
                        detector_code="COMP-D1",
                        detector_name="",
                        category=AnomalyCategory.COMPLIANCE,
                        severity=0.6,
                        confidence=0.8,
                        evidence={},
                        explanation="",
                        next_review_action="",
                    )
                )

    df_works = pd.DataFrame(works)
    det = EntityRecurrenceDetector(min_anomalies=3, min_exposure=3)
    findings = det.detect(df_works, prior)

    by_entity = {f.evidence["entity_name"]: f for f in findings}
    assert "SMALL_IA" in by_entity
    assert "LARGE_IA" in by_entity

    small_f = by_entity["SMALL_IA"]
    large_f = by_entity["LARGE_IA"]

    # SMALL_IA has higher excess failure rate -> higher severity
    assert small_f.severity >= large_f.severity
    # LARGE_IA has larger sample size -> higher confidence
    assert large_f.confidence > small_f.confidence


def test_recurrence_no_silent_fallback_to_raw_k():
    """Verifies that an entity with k >= 3 is not flagged if it does not exceed peer expectation."""
    works = []
    prior = []
    # Entity with N=100, k=5 (5% failure rate)
    for i in range(100):
        rid = f"SAFE_{i}"
        works.append(
            {
                "WORK_RECOMMENDATION_DTL_ID": rid,
                "ia_name": "SAFE_IA",
                "STATE_NAME": "MP",
                "IDA_NAME": "BHOPAL",
                "SANCTION_AMOUNT": 100000.0,
            }
        )
        if i < 5:
            prior.append(
                Finding(
                    finding_id=f"F_SAFE_{i}",
                    work_id=rid,
                    work_rec_id=rid,
                    detector_code="COMP-D1",
                    detector_name="",
                    category=AnomalyCategory.COMPLIANCE,
                    severity=0.5,
                    confidence=0.8,
                    evidence={},
                    explanation="",
                    next_review_action="",
                )
            )

    # Peers with 30% failure rate
    for a in range(5):
        for w in range(20):
            rid = f"P_{a}_{w}"
            works.append(
                {
                    "WORK_RECOMMENDATION_DTL_ID": rid,
                    "ia_name": f"PEER_{a}",
                    "STATE_NAME": "MP",
                    "IDA_NAME": "BHOPAL",
                    "SANCTION_AMOUNT": 100000.0,
                }
            )
            if w < 6:
                prior.append(
                    Finding(
                        finding_id=f"FP_{a}_{w}",
                        work_id=rid,
                        work_rec_id=rid,
                        detector_code="COMP-D1",
                        detector_name="",
                        category=AnomalyCategory.COMPLIANCE,
                        severity=0.5,
                        confidence=0.8,
                        evidence={},
                        explanation="",
                        next_review_action="",
                    )
                )

    df_works = pd.DataFrame(works)
    det = EntityRecurrenceDetector(min_anomalies=3, min_exposure=3)
    findings = det.detect(df_works, prior)

    flagged = {f.evidence["entity_name"] for f in findings}
    assert "SAFE_IA" not in flagged, "Entity with k=5 >= 3 but failure rate 5% vs 30% baseline must NOT be flagged"


def test_trend_analyzer():
    df = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": f"60{i}",
                "SANCTION_DATE": pd.Timestamp(f"2023-0{i % 5 + 1}-15"),
                "SANCTION_AMOUNT": 500000.0,
                "days_rec_to_sanction": 30.0 + i,
                "ACTUAL_END_DATE": pd.Timestamp("2024-01-01") if i % 2 == 0 else pd.NaT,
                "total_disbursed": 500000.0,
                "WORK_CATEGORY": "Education",
            }
            for i in range(10)
        ]
    )

    trends = TrendAnalyzer.compute_yearly_trends(df)
    assert not trends.empty
    assert "avg_sanction_delay" in trends.columns
    assert "completion_rate_pct" in trends.columns


def test_vendor_recurrence_empirical_bayes():
    """Verifies that repeat contractor/vendor anomalies trigger REC-D15 with proper attribution."""
    works = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": f"V_{i}",
                "primary_vendor": "SHADY_CONTRACTOR_LTD", "primary_vendor_id": "V_SHADY",
                "STATE_NAME": "RAJASTHAN",
                "IDA_NAME": "JAIPUR",
                "SANCTION_AMOUNT": 800000.0,
            }
            for i in range(5)
        ]
    )
    prior = [
        Finding(
            finding_id=f"FV_{i}",
            work_id=f"V_{i}",
            work_rec_id=f"V_{i}",
            detector_code="FIN-D6",
            detector_name="Cost Overrun",
            category=AnomalyCategory.FINANCIAL,
            severity=0.85,
            confidence=0.90,
            evidence={},
            explanation="Cost overrun detected.",
            next_review_action="Audit invoices.",
        )
        for i in range(4)
    ]

    det = EntityRecurrenceDetector(min_anomalies=3, min_exposure=3)
    findings = det.detect(works, prior)

    assert len(findings) == 4
    assert all(f.detector_code == "REC-D15" for f in findings)
    assert all(f.evidence["entity_type"] == "VENDOR" for f in findings)
    assert all(f.evidence["entity_name"] == "SHADY_CONTRACTOR_LTD" for f in findings)
    assert all(f.category == AnomalyCategory.FINANCIAL for f in findings)
    assert {f.work_rec_id for f in findings} == {"V_0", "V_1", "V_2", "V_3"}
    assert "SHADY_CONTRACTOR_LTD" in findings[0].explanation
