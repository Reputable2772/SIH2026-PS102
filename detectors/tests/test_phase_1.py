"""
Test Suite for Phase 1: Baselines & Core Detection Engine.
"""

import numpy as np
import pandas as pd
import pytest

from src.engine.baselines import BaselineEngine
from src.engine.detectors import CoreDetectionEngine
from src.engine.detectors.compliance import (
    ExecutionDeadlineDetector,
    SanctionSLABreachDetector,
    StalledDisbursementDetector,
)
from src.engine.detectors.financial import CostOverrunDetector


@pytest.fixture
def sample_works():
    """Constructs representative canonical works covering all anomaly archetypes."""
    return pd.DataFrame(
        [
            # 1. Normal Completed Work
            {
                "WORK_RECOMMENDATION_DTL_ID": "101",
                "WORK_ID": "W101",
                "STATE_NAME": "DELHI",
                "IDA_NAME": "CENTRAL DELHI",
                "WORK_CATEGORY": "Education",
                "SANCTION_AMOUNT": 500000.0,
                "RECOMMENDATION_DATE": pd.Timestamp("2025-01-01"),
                "SANCTION_DATE": pd.Timestamp("2025-01-20"),
                "ACTUAL_END_DATE": pd.Timestamp("2025-06-01"),
                "days_rec_to_sanction": 19,
                "days_sanction_to_completion": 132,
                "days_since_sanction": 250,
                "total_disbursed": 500000.0,
                "payment_count": 2,
                "first_payment_date": pd.Timestamp("2025-02-01"),
                "last_payment_date": pd.Timestamp("2025-05-01"),
                "house": "LOK_SABHA",
                "dqi_score": 0.95,
                "ia_name": "PWD",
            },
            # 2. Sanction SLA Breach (90 days > 45)
            {
                "WORK_RECOMMENDATION_DTL_ID": "102",
                "WORK_ID": "W102",
                "STATE_NAME": "DELHI",
                "IDA_NAME": "NORTH DELHI",
                "WORK_CATEGORY": "Education",
                "SANCTION_AMOUNT": 500000.0,
                "RECOMMENDATION_DATE": pd.Timestamp("2025-01-01"),
                "SANCTION_DATE": pd.Timestamp("2025-04-01"),
                "ACTUAL_END_DATE": pd.NaT,
                "days_rec_to_sanction": 90,
                "days_sanction_to_completion": np.nan,
                "days_since_sanction": 150,
                "total_disbursed": 0.0,
                "payment_count": 0,
                "first_payment_date": pd.NaT,
                "last_payment_date": pd.NaT,
                "house": "LOK_SABHA",
                "dqi_score": 0.85,
                "ia_name": "PWD",
            },
            # 3. Execution Deadline Breach (500 days > 365)
            {
                "WORK_RECOMMENDATION_DTL_ID": "103",
                "WORK_ID": "W103",
                "STATE_NAME": "DELHI",
                "IDA_NAME": "SOUTH DELHI",
                "WORK_CATEGORY": "Roads",
                "SANCTION_AMOUNT": 1000000.0,
                "RECOMMENDATION_DATE": pd.Timestamp("2024-01-01"),
                "SANCTION_DATE": pd.Timestamp("2024-02-01"),
                "ACTUAL_END_DATE": pd.NaT,
                "days_rec_to_sanction": 31,
                "days_sanction_to_completion": np.nan,
                "days_since_sanction": 500,
                "total_disbursed": 300000.0,
                "payment_count": 1,
                "first_payment_date": pd.Timestamp("2024-04-01"),
                "last_payment_date": pd.Timestamp("2024-04-01"),
                "house": "LOK_SABHA",
                "dqi_score": 0.90,
                "ia_name": "CPWD",
            },
            # 4. Stalled Disbursement (120 days since sanction, 0 disbursed)
            {
                "WORK_RECOMMENDATION_DTL_ID": "104",
                "WORK_ID": "W104",
                "STATE_NAME": "DELHI",
                "IDA_NAME": "EAST DELHI",
                "WORK_CATEGORY": "Health",
                "SANCTION_AMOUNT": 800000.0,
                "RECOMMENDATION_DATE": pd.Timestamp("2025-01-01"),
                "SANCTION_DATE": pd.Timestamp("2025-01-20"),
                "ACTUAL_END_DATE": pd.NaT,
                "days_rec_to_sanction": 19,
                "days_sanction_to_completion": np.nan,
                "days_since_sanction": 120,
                "total_disbursed": 0.0,
                "payment_count": 0,
                "first_payment_date": pd.NaT,
                "last_payment_date": pd.NaT,
                "house": "LOK_SABHA",
                "dqi_score": 0.88,
                "ia_name": "MCD",
            },
            # 5. Cost Overrun (₹1,500,000 disbursed on ₹1,000,000 sanction = 150%)
            {
                "WORK_RECOMMENDATION_DTL_ID": "105",
                "WORK_ID": "W105",
                "STATE_NAME": "DELHI",
                "IDA_NAME": "WEST DELHI",
                "WORK_CATEGORY": "Roads",
                "SANCTION_AMOUNT": 1000000.0,
                "RECOMMENDATION_DATE": pd.Timestamp("2025-01-01"),
                "SANCTION_DATE": pd.Timestamp("2025-01-20"),
                "ACTUAL_END_DATE": pd.Timestamp("2025-08-01"),
                "days_rec_to_sanction": 19,
                "days_sanction_to_completion": 193,
                "days_since_sanction": 200,
                "total_disbursed": 1500000.0,
                "payment_count": 3,
                "first_payment_date": pd.Timestamp("2025-03-01"),
                "last_payment_date": pd.Timestamp("2025-07-01"),
                "house": "LOK_SABHA",
                "dqi_score": 0.92,
                "ia_name": "PWD",
            },
        ]
    )


def test_baseline_engine():
    # Synthetic cohort
    data = []
    for i in range(25):
        data.append(
            {
                "STATE_NAME": "KERALA",
                "WORK_CATEGORY": "Drinking Water",
                "SANCTION_AMOUNT": 200000.0 + i * 5000.0,
                "days_rec_to_sanction": 20 + i,
                "days_sanction_to_completion": 150 + i,
            }
        )
    df = pd.DataFrame(data)

    engine = BaselineEngine(min_sample_size=10)
    engine.fit(df)

    base, conf = engine.get_peer_baseline("KERALA", "Drinking Water")
    assert base is not None
    assert base.sample_size == 25
    assert conf > 0.40
    assert base.cost_median > 0


def test_compliance_detectors(sample_works):
    d1 = SanctionSLABreachDetector(sla_days=45)
    f1 = d1.detect(sample_works)
    assert len(f1) == 1
    assert f1[0].work_rec_id == "102"
    assert "45-day deadline" in f1[0].explanation
    assert len(f1[0].next_review_action) > 10

    d2 = ExecutionDeadlineDetector(ls_sla=365, rs_sla=540)
    f2 = d2.detect(sample_works)
    assert len(f2) == 1
    assert f2[0].work_rec_id == "103"

    d3 = StalledDisbursementDetector(stall_days=90)
    f3 = d3.detect(sample_works)
    assert len(f3) == 2  # Work 102 and Work 104 are both > 90 days with 0 disbursed


def test_financial_cost_overrun_detector(sample_works):
    d6 = CostOverrunDetector(threshold_ratio=1.05)
    f6 = d6.detect(sample_works)
    assert len(f6) == 1
    assert f6[0].work_rec_id == "105"
    assert f6[0].evidence["overrun_ratio"] == 1.5


def test_core_detection_engine_run(sample_works):
    engine = CoreDetectionEngine()
    engine.fit_baselines(sample_works)
    findings = engine.run(sample_works)

    assert len(findings) > 0
    for f in findings:
        assert 0.0 <= f.severity <= 1.0
        assert 0.0 <= f.confidence <= 1.0
        assert len(f.evidence) > 0
        assert len(f.explanation) > 0
        assert len(f.next_review_action) > 0  # Mandated by AC-19

# --- Added for Missing Coverage (FIN-D8, AGY-D11, FIN-D5, EXEC-D9) ---
from src.engine.detectors.agency import IAOverloadDetector
from src.engine.detectors.execution import ProgressExpenditureMismatchDetector
from src.engine.detectors.financial import CostPeerOutlierDetector, TemporalDisbursementSpikeDetector


def test_temporal_disbursement_spike_detector():
    """Validates FIN-D8 flags >1M disbursed across >=3 payments in <=7 days."""
    df = pd.DataFrame([
        {
            "WORK_RECOMMENDATION_DTL_ID": "201",
            "total_disbursed": 1500000.0,
            "payment_count": 4,
            "first_payment_date": pd.Timestamp("2026-03-25"),
            "last_payment_date": pd.Timestamp("2026-03-31"), # 6 days span
        },
        {
            "WORK_RECOMMENDATION_DTL_ID": "202", # Normal span
            "total_disbursed": 1500000.0,
            "payment_count": 4,
            "first_payment_date": pd.Timestamp("2026-01-01"),
            "last_payment_date": pd.Timestamp("2026-06-01"),
        }
    ])
    d = TemporalDisbursementSpikeDetector()
    findings = d.detect(df)
    assert len(findings) == 1
    assert findings[0].work_rec_id == "201"

def test_ia_overload_detector():
    """Validates AGY-D11 flags agencies with >=10 delayed works and >=5M disbursed."""
    records = []
    # 12 overloaded works for one agency
    for i in range(12):
        records.append({
            "WORK_RECOMMENDATION_DTL_ID": f"30{i}",
            "ia_name": "OVERLOADED_PWD",
            "IDA_NAME": "DISTRICT_A",
            "days_since_sanction": 400, # > 365
            "ACTUAL_END_DATE": pd.NaT,
            "total_disbursed": 500000.0
        })
    df = pd.DataFrame(records)
    d = IAOverloadDetector(min_delayed_works=10, min_total_expenditure=5000000.0)
    findings = d.detect(df)
    assert len(findings) == 12 # Flags all works belonging to the IA
    assert findings[0].evidence["agency_delayed_works"] == 12

def test_cost_peer_outlier_detector():
    """Validates FIN-D5 correctly normalizes IQR and flags >2.5 Z-score anomalies."""
    df = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "401",
        "STATE_NAME": "TEST_STATE",
        "WORK_CATEGORY": "Education",
        "SANCTION_AMOUNT": 8500000.0 # Massive outlier
    }])

    # Mock baseline engine with 500k median cost
    class MockBaseline:
        def get_peer_baseline(self, state, cat):
            from dataclasses import dataclass
            @dataclass
            class Base:
                sample_size: int = 50
                cost_median: float = 500000.0
                cost_iqr: float = 100000.0
                cost_std: float = 80000.0
                cohort_key: tuple = ("TEST_STATE", "Education")
            return Base(), 1.0

    d = CostPeerOutlierDetector(z_threshold=2.5)
    findings = d.detect(df, MockBaseline())
    assert len(findings) == 1
    assert findings[0].work_rec_id == "401"

def test_progress_expenditure_mismatch_detector():
    """Validates EXEC-D9 flags works >365d old with >=85% funds disbursed but no completion."""
    df = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "501",
        "SANCTION_AMOUNT": 1000000.0,
        "total_disbursed": 900000.0, # 90%
        "days_since_sanction": 400,
        "ACTUAL_END_DATE": pd.NaT
    }])
    d = ProgressExpenditureMismatchDetector(min_ratio=0.85, min_days=365)
    findings = d.detect(df)
    assert len(findings) == 1
    assert findings[0].work_rec_id == "501"

