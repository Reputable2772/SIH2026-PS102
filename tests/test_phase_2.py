"""
Test Suite for Phase 2: Cross-Work, Entity & Pattern Intelligence.
"""

import pytest
import pandas as pd
import numpy as np
from src.engine.detectors.base import Finding, AnomalyCategory
from src.engine.cross_work.similarity import DuplicateWorkDetector
from src.engine.cross_work.concentration import AgencyConcentrationDetector, VendorConcentrationDetector
from src.engine.cross_work.recurrence import EntityRecurrenceDetector
from src.engine.cross_work.trends import TrendAnalyzer
from src.engine.cross_work import CrossWorkIntelligenceEngine


def test_duplicate_work_detector():
    df = pd.DataFrame([
        {
            "WORK_RECOMMENDATION_DTL_ID": "201",
            "WORK_ID": "W201",
            "STATE_NAME": "PUNJAB",
            "IDA_NAME": "AMRITSAR",
            "WORK_CATEGORY": "Community Halls",
            "WORK_DESCRIPTION": "Construction of modern community hall near Gurudwara Sahib block A",
            "SANCTION_AMOUNT": 1500000.0,
            "dqi_score": 0.90
        },
        {
            "WORK_RECOMMENDATION_DTL_ID": "202",
            "WORK_ID": "W202",
            "STATE_NAME": "PUNJAB",
            "IDA_NAME": "AMRITSAR",
            "WORK_CATEGORY": "Community Halls",
            "WORK_DESCRIPTION": "Construction of modern community hall near Gurudwara Sahib block A with veranda",
            "SANCTION_AMOUNT": 1520000.0,
            "dqi_score": 0.90
        },
        {
            "WORK_RECOMMENDATION_DTL_ID": "203",
            "WORK_ID": "W203",
            "STATE_NAME": "PUNJAB",
            "IDA_NAME": "AMRITSAR",
            "WORK_CATEGORY": "Community Halls",
            "WORK_DESCRIPTION": "Laying of underground sewerage pipe network at sector 4",
            "SANCTION_AMOUNT": 800000.0,
            "dqi_score": 0.90
        }
    ])

    detector = DuplicateWorkDetector(similarity_threshold=0.75, cost_window_ratio=0.20)
    findings = detector.detect(df)

    assert len(findings) >= 1
    f = findings[0]
    assert f.detector_code == "SIM-D12"
    assert "202" in f.evidence["matched_work_rec_id"] or "201" in f.evidence["matched_work_rec_id"]
    assert f.evidence["same_district"] == True
    assert len(f.next_review_action) > 0


def test_agency_concentration_detector():
    records = []
    # 20 works in district, 16 assigned to same IA (80% share)
    for i in range(20):
        ia = "DOMINANT_PWD" if i < 16 else "OTHER_AGENCY"
        records.append({
            "WORK_RECOMMENDATION_DTL_ID": f"30{i}",
            "WORK_ID": f"W30{i}",
            "STATE_NAME": "HARYANA",
            "IDA_NAME": "GURGAON",
            "ia_name": ia,
            "SANCTION_AMOUNT": 500000.0
        })
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
        records.append({
            "WORK_RECOMMENDATION_DTL_ID": f"40{i}",
            "WORK_ID": f"W40{i}",
            "STATE_NAME": "RAJASTHAN",
            "IDA_NAME": "JAIPUR",
            "primary_vendor": vendor,
            "total_disbursed": disb,
            "SANCTION_AMOUNT": disb
        })
    df = pd.DataFrame(records)

    detector = VendorConcentrationDetector(share_threshold=0.50, min_vendor_works=5)
    findings = detector.detect(df)

    assert len(findings) > 0
    f = findings[0]
    assert f.detector_code == "VND-D14"
    assert f.evidence["vendor_name"] == "MONOPOLY_CONSTRUCTION"
    assert f.evidence["vendor_share_pct"] > 50.0


def test_entity_recurrence_detector():
    works = pd.DataFrame([
        {"WORK_RECOMMENDATION_DTL_ID": "501", "ia_name": "REPEAT_IA", "STATE_NAME": "BIHAR", "IDA_NAME": "PATNA", "SANCTION_AMOUNT": 500000.0},
        {"WORK_RECOMMENDATION_DTL_ID": "502", "ia_name": "REPEAT_IA", "STATE_NAME": "BIHAR", "IDA_NAME": "PATNA", "SANCTION_AMOUNT": 500000.0},
        {"WORK_RECOMMENDATION_DTL_ID": "503", "ia_name": "REPEAT_IA", "STATE_NAME": "BIHAR", "IDA_NAME": "PATNA", "SANCTION_AMOUNT": 500000.0}
    ])

    # Prior findings across all 3 works
    prior = [
        Finding(
            finding_id="F1", work_id="501", work_rec_id="501", detector_code="COMP-D1",
            detector_name="Turnaround", category=AnomalyCategory.COMPLIANCE, severity=0.7,
            confidence=0.8, evidence={}, explanation="", next_review_action=""
        ),
        Finding(
            finding_id="F2", work_id="502", work_rec_id="502", detector_code="FIN-D5",
            detector_name="Cost", category=AnomalyCategory.FINANCIAL, severity=0.8,
            confidence=0.8, evidence={}, explanation="", next_review_action=""
        ),
        Finding(
            finding_id="F3", work_id="503", work_rec_id="503", detector_code="COMP-D2",
            detector_name="Delay", category=AnomalyCategory.COMPLIANCE, severity=0.75,
            confidence=0.8, evidence={}, explanation="", next_review_action=""
        )
    ]

    detector = EntityRecurrenceDetector(min_anomalies=3)
    findings = detector.detect(works, prior)

    assert len(findings) == 1
    assert findings[0].detector_code == "REC-D15"
    assert findings[0].evidence["entity_name"] == "REPEAT_IA"
    assert findings[0].evidence["flagged_works_count"] == 3


def test_trend_analyzer():
    df = pd.DataFrame([
        {
            "WORK_RECOMMENDATION_DTL_ID": f"60{i}",
            "SANCTION_DATE": pd.Timestamp(f"2023-0{i%5+1}-15"),
            "SANCTION_AMOUNT": 500000.0,
            "days_rec_to_sanction": 30.0 + i,
            "ACTUAL_END_DATE": pd.Timestamp("2024-01-01") if i % 2 == 0 else pd.NaT,
            "total_disbursed": 500000.0,
            "WORK_CATEGORY": "Education"
        }
        for i in range(10)
    ])

    trends = TrendAnalyzer.compute_yearly_trends(df)
    assert not trends.empty
    assert "avg_sanction_delay" in trends.columns
    assert "completion_rate_pct" in trends.columns
