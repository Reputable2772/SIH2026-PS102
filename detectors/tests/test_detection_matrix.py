"""
Matrix and Archetype Test Suite for All MPLADS Detection Mechanisms.

Tests every detector against:
1. Targeted synthetic archetype rows (positive and negative cases for each fraud/anomaly type).
2. Live canonical rows from the real e-SAKSHI dataset.
3. Stress-testing across randomly generated and mutated work records.
"""

import pytest
import pandas as pd
import numpy as np
from src.config import PROCESSED_DIR
from src.engine.detectors.compliance import (
    SanctionSLABreachDetector,
    ExecutionDeadlineDetector,
    StalledDisbursementDetector,
    LifecycleLeapDetector
)
from src.engine.detectors.financial import (
    CostPeerOutlierDetector,
    CostOverrunDetector
)
from src.engine.detectors.execution import ProgressExpenditureMismatchDetector
from src.engine.baselines import BaselineEngine
from src.engine.detectors.base import Finding


@pytest.fixture(scope="module")
def fitted_baseline_engine():
    """Builds a BaselineEngine fitted on standard reference categories."""
    df_ref = pd.DataFrame([
        {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 500000.0},
        {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 520000.0},
        {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 480000.0},
        {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 510000.0},
        {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 490000.0},
        {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 505000.0},
    ])
    be = BaselineEngine()
    be.fit(df_ref)
    return be


# ---------------------------------------------------------------------------
# 1. Targeted Row Archetype Tests (Pass / Fail per Anomaly Type)
# ---------------------------------------------------------------------------

def test_archetype_comp_d1_sanction_sla():
    """Tests COMP-D1: Sanction Turnaround SLA (>45d)."""
    det = SanctionSLABreachDetector()
    # Positive case: 90 days delay (> 45d)
    pos_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "POS_D1",
        "WORK_ID": "W_POS_D1",
        "days_rec_to_sanction": 90,
        "RECOMMENDATION_DATE": "2024-01-01",
        "SANCTION_DATE": "2024-03-31",
        "dqi_score": 1.0
    }])
    # Negative case: 20 days delay (<= 45d)
    neg_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "NEG_D1",
        "WORK_ID": "W_NEG_D1",
        "days_rec_to_sanction": 20,
        "RECOMMENDATION_DATE": "2024-01-01",
        "SANCTION_DATE": "2024-01-21",
        "dqi_score": 1.0
    }])

    pos_findings = det.detect(pos_row)
    neg_findings = det.detect(neg_row)

    assert len(pos_findings) == 1
    assert pos_findings[0].detector_code == "COMP-D1"
    assert "45-day deadline" in pos_findings[0].explanation
    assert len(neg_findings) == 0


def test_archetype_comp_d2_execution_sla():
    """Tests COMP-D2: Execution SLA (>365d for LS)."""
    det = ExecutionDeadlineDetector()
    # Positive case: 500 days completion
    pos_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "POS_D2",
        "WORK_ID": "W_POS_D2",
        "house": "LOK_SABHA",
        "days_sanction_to_completion": 500,
        "days_since_sanction": 500,
        "ACTUAL_END_DATE": "2024-05-01",
        "SANCTION_DATE": "2022-12-15",
        "dqi_score": 1.0
    }])
    # Negative case: 180 days completion
    neg_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "NEG_D2",
        "WORK_ID": "W_NEG_D2",
        "house": "LOK_SABHA",
        "days_sanction_to_completion": 180,
        "days_since_sanction": 180,
        "ACTUAL_END_DATE": "2023-06-15",
        "SANCTION_DATE": "2022-12-15",
        "dqi_score": 1.0
    }])

    pos_findings = det.detect(pos_row)
    neg_findings = det.detect(neg_row)

    assert len(pos_findings) == 1
    assert pos_findings[0].detector_code == "COMP-D2"
    assert len(neg_findings) == 0


def test_archetype_comp_d3_stalled_disbursement():
    """Tests COMP-D3: Zero disbursement 90+ days after sanction."""
    det = StalledDisbursementDetector()
    # Positive case: 120 days post-sanction, zero disbursed, incomplete
    pos_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "POS_D3",
        "WORK_ID": "W_POS_D3",
        "days_since_sanction": 120,
        "total_disbursed": 0.0,
        "SANCTION_DATE": "2024-01-01",
        "ACTUAL_END_DATE": None,
        "dqi_score": 1.0
    }])
    # Negative case: 120 days post-sanction, but disbursed funds
    neg_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "NEG_D3",
        "WORK_ID": "W_NEG_D3",
        "days_since_sanction": 120,
        "total_disbursed": 250000.0,
        "SANCTION_DATE": "2024-01-01",
        "ACTUAL_END_DATE": None,
        "dqi_score": 1.0
    }])

    assert len(det.detect(pos_row)) == 1
    assert len(det.detect(neg_row)) == 0


def test_archetype_comp_d4_lifecycle_leap():
    """Tests COMP-D4: Retroactive sanction / disbursement before sanction."""
    det = LifecycleLeapDetector()
    # Positive case: sanction before recommendation (retroactive)
    pos_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "POS_D4",
        "WORK_ID": "W_POS_D4",
        "is_retroactive_sanction": True,
        "is_disbursement_before_sanction": False,
        "is_completion_before_sanction": False,
        "RECOMMENDATION_DATE": "2024-05-01",
        "SANCTION_DATE": "2024-04-01",
        "dqi_score": 1.0
    }])
    # Negative case: proper sequence
    neg_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "NEG_D4",
        "WORK_ID": "W_NEG_D4",
        "is_retroactive_sanction": False,
        "is_disbursement_before_sanction": False,
        "is_completion_before_sanction": False,
        "RECOMMENDATION_DATE": "2024-04-01",
        "SANCTION_DATE": "2024-05-01",
        "dqi_score": 1.0
    }])

    assert len(det.detect(pos_row)) == 1
    assert len(det.detect(neg_row)) == 0


def test_archetype_fin_d5_cost_peer_outlier(fitted_baseline_engine):
    """Tests FIN-D5: Cost outlier relative to peer median."""
    det = CostPeerOutlierDetector()
    # Peer median is 505k, IQR is ~25k. 2.5 million is a massive outlier
    pos_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "POS_D5",
        "WORK_ID": "W_POS_D5",
        "STATE_NAME": "DELHI",
        "WORK_CATEGORY": "ROADS",
        "SANCTION_AMOUNT": 2500000.0,
        "dqi_score": 1.0
    }])
    # Normal cost around 510k
    neg_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "NEG_D5",
        "WORK_ID": "W_NEG_D5",
        "STATE_NAME": "DELHI",
        "WORK_CATEGORY": "ROADS",
        "SANCTION_AMOUNT": 510000.0,
        "dqi_score": 1.0
    }])

    pos_findings = det.detect(pos_row, baseline_engine=fitted_baseline_engine)
    neg_findings = det.detect(neg_row, baseline_engine=fitted_baseline_engine)

    assert len(pos_findings) == 1
    assert pos_findings[0].detector_code == "FIN-D5"
    assert len(neg_findings) == 0


def test_archetype_fin_d6_cost_overrun():
    """Tests FIN-D6: Total disbursements exceeding sanction amount (>5%)."""
    det = CostOverrunDetector()
    # Positive case: 1.5M disbursed on 1.0M sanction (50% overrun)
    pos_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "POS_D6",
        "WORK_ID": "W_POS_D6",
        "SANCTION_AMOUNT": 1000000.0,
        "total_disbursed": 1500000.0,
        "dqi_score": 1.0
    }])
    # Negative case: 950k disbursed on 1.0M sanction
    neg_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "NEG_D6",
        "WORK_ID": "W_NEG_D6",
        "SANCTION_AMOUNT": 1000000.0,
        "total_disbursed": 950000.0,
        "dqi_score": 1.0
    }])

    assert len(det.detect(pos_row)) == 1
    assert len(det.detect(neg_row)) == 0


def test_archetype_exec_d9_progress_mismatch():
    """Tests EXEC-D9: >85% disbursed and >365d elapsed, but not marked complete."""
    det = ProgressExpenditureMismatchDetector()
    # Positive case: 90% disbursed, 400 days, incomplete
    pos_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "POS_D9",
        "WORK_ID": "W_POS_D9",
        "SANCTION_AMOUNT": 1000000.0,
        "total_disbursed": 900000.0,
        "days_since_sanction": 400,
        "ACTUAL_END_DATE": None,
        "dqi_score": 1.0
    }])
    # Negative case: completed
    neg_row = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "NEG_D9",
        "WORK_ID": "W_NEG_D9",
        "SANCTION_AMOUNT": 1000000.0,
        "total_disbursed": 900000.0,
        "days_since_sanction": 400,
        "ACTUAL_END_DATE": "2024-01-01",
        "dqi_score": 1.0
    }])

    assert len(det.detect(pos_row)) == 1
    assert len(det.detect(neg_row)) == 0


# ---------------------------------------------------------------------------
# 2. Random Synthetic Stress Testing Across All Detectors
# ---------------------------------------------------------------------------

def test_random_synthetic_works_no_crashes(fitted_baseline_engine):
    """Generates 50 randomized synthetic works and verifies detector robustness & zero crash."""
    np.random.seed(42)
    n = 50

    states = ["DELHI", "MAHARASHTRA", "UTTAR PRADESH", "TAMIL NADU"]
    categories = ["ROADS", "DRINKING_WATER", "EDUCATION", "HEALTH"]

    random_df = pd.DataFrame({
        "WORK_RECOMMENDATION_DTL_ID": [f"RND_{i}" for i in range(n)],
        "WORK_ID": [f"W_RND_{i}" for i in range(n)],
        "STATE_NAME": np.random.choice(states, n),
        "IDA_NAME": [f"DIST_{i%5}" for i in range(n)],
        "WORK_CATEGORY": np.random.choice(categories, n),
        "SANCTION_AMOUNT": np.random.uniform(50000, 5000000, n),
        "total_disbursed": np.random.uniform(0, 6000000, n),
        "days_rec_to_sanction": np.random.randint(-10, 200, n),
        "days_since_sanction": np.random.randint(0, 800, n),
        "days_sanction_to_completion": [None if i % 2 == 0 else np.random.randint(50, 600) for i in range(n)],
        "ACTUAL_END_DATE": [None if i % 2 == 0 else "2024-06-01" for i in range(n)],
        "SANCTION_DATE": ["2023-01-15"] * n,
        "RECOMMENDATION_DATE": ["2022-12-01"] * n,
        "house": np.random.choice(["LOK_SABHA", "RAJYA_SABHA"], n),
        "is_retroactive_sanction": np.random.choice([True, False], n, p=[0.05, 0.95]),
        "is_disbursement_before_sanction": False,
        "is_completion_before_sanction": False,
        "ia_name": [f"AGENCY_{i%4}" for i in range(n)],
        "primary_vendor": [f"VENDOR_{i%6}" for i in range(n)],
        "dqi_score": np.random.uniform(0.5, 1.0, n)
    })

    # Execute all detectors
    detectors = [
        SanctionSLABreachDetector(),
        ExecutionDeadlineDetector(),
        StalledDisbursementDetector(),
        LifecycleLeapDetector(),
        CostPeerOutlierDetector(),
        CostOverrunDetector(),
        ProgressExpenditureMismatchDetector()
    ]

    all_findings = []
    for det in detectors:
        if isinstance(det, CostPeerOutlierDetector):
            f = det.detect(random_df, baseline_engine=fitted_baseline_engine)
        else:
            f = det.detect(random_df)
        all_findings.extend(f)

    assert isinstance(all_findings, list)
    # Findings should have valid format
    for f in all_findings:
        assert isinstance(f, Finding)
        assert 0.0 <= f.severity <= 1.0
        assert 0.0 <= f.confidence <= 1.0
        assert f.next_review_action != ""


# ---------------------------------------------------------------------------
# 3. Live Test on Real Canonical Works Sample
# ---------------------------------------------------------------------------

def test_live_canonical_dataset_rows():
    """Pulls real rows from processed canonical data and verifies detector execution."""
    parquet_path = PROCESSED_DIR / "canonical_works.parquet"
    if not parquet_path.exists():
        pytest.skip("Processed canonical parquet not found")

    df = pd.read_parquet(parquet_path)
    sample_df = df.sample(n=min(100, len(df)), random_state=42).reset_index(drop=True)

    be = BaselineEngine().fit(sample_df)
    det = CostPeerOutlierDetector()
    findings = det.detect(sample_df, baseline_engine=be)

    assert isinstance(findings, list)
