"""
Matrix and Archetype Test Suite for All MPLADS Detection Mechanisms.

Tests every detector against:
1. Targeted synthetic archetype rows (positive and negative cases for each fraud/anomaly type).
2. Live canonical rows from the real e-SAKSHI dataset.
3. Stress-testing across randomly generated and mutated work records.
"""

import numpy as np
import pandas as pd
import pytest

from src.config import PROCESSED_DIR
from src.engine.baselines import BaselineEngine
from src.engine.detectors.base import Finding
from src.engine.detectors.compliance import (
    ExecutionDeadlineDetector,
    LifecycleLeapDetector,
    SanctionSLABreachDetector,
    StalledDisbursementDetector,
)
from src.engine.detectors.execution import ProgressExpenditureMismatchDetector
from src.engine.detectors.financial import CostOverrunDetector, CostPeerOutlierDetector


@pytest.fixture(scope="module")
def fitted_baseline_engine():
    """Builds a BaselineEngine fitted on standard reference categories."""
    df_ref = pd.DataFrame(
        [
            {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 500000.0},
            {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 520000.0},
            {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 480000.0},
            {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 510000.0},
            {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 490000.0},
            {"STATE_NAME": "DELHI", "WORK_CATEGORY": "ROADS", "SANCTION_AMOUNT": 505000.0},
        ]
    )
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
    pos_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "POS_D1",
                "WORK_ID": "W_POS_D1",
                "days_rec_to_sanction": 90,
                "RECOMMENDATION_DATE": "2024-01-01",
                "SANCTION_DATE": "2024-03-31",
                "dqi_score": 1.0,
            }
        ]
    )
    # Negative case: 20 days delay (<= 45d)
    neg_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "NEG_D1",
                "WORK_ID": "W_NEG_D1",
                "days_rec_to_sanction": 20,
                "RECOMMENDATION_DATE": "2024-01-01",
                "SANCTION_DATE": "2024-01-21",
                "dqi_score": 1.0,
            }
        ]
    )

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
    pos_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "POS_D2",
                "WORK_ID": "W_POS_D2",
                "house": "LOK_SABHA",
                "days_sanction_to_completion": 500,
                "days_since_sanction": 500,
                "ACTUAL_END_DATE": "2024-05-01",
                "SANCTION_DATE": "2022-12-15",
                "dqi_score": 1.0,
            }
        ]
    )
    # Negative case: 180 days completion
    neg_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "NEG_D2",
                "WORK_ID": "W_NEG_D2",
                "house": "LOK_SABHA",
                "days_sanction_to_completion": 180,
                "days_since_sanction": 180,
                "ACTUAL_END_DATE": "2023-06-15",
                "SANCTION_DATE": "2022-12-15",
                "dqi_score": 1.0,
            }
        ]
    )

    pos_findings = det.detect(pos_row)
    neg_findings = det.detect(neg_row)

    assert len(pos_findings) == 1
    assert pos_findings[0].detector_code == "COMP-D2"
    assert len(neg_findings) == 0


def test_archetype_comp_d3_stalled_disbursement():
    """Tests COMP-D3: Zero disbursement 90+ days after sanction."""
    det = StalledDisbursementDetector()
    # Positive case: 120 days post-sanction, zero disbursed, incomplete
    pos_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "POS_D3",
                "WORK_ID": "W_POS_D3",
                "days_since_sanction": 120,
                "total_disbursed": 0.0,
                "SANCTION_DATE": "2024-01-01",
                "ACTUAL_END_DATE": None,
                "dqi_score": 1.0,
            }
        ]
    )
    # Negative case: 120 days post-sanction, but disbursed funds
    neg_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "NEG_D3",
                "WORK_ID": "W_NEG_D3",
                "days_since_sanction": 120,
                "total_disbursed": 250000.0,
                "SANCTION_DATE": "2024-01-01",
                "ACTUAL_END_DATE": None,
                "dqi_score": 1.0,
            }
        ]
    )

    assert len(det.detect(pos_row)) == 1
    assert len(det.detect(neg_row)) == 0


def test_archetype_comp_d4_lifecycle_leap():
    """Tests COMP-D4: Retroactive sanction / disbursement before sanction."""
    det = LifecycleLeapDetector()
    # Positive case: sanction before recommendation (retroactive)
    pos_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "POS_D4",
                "WORK_ID": "W_POS_D4",
                "is_retroactive_sanction": True,
                "is_disbursement_before_sanction": False,
                "is_completion_before_sanction": False,
                "RECOMMENDATION_DATE": "2024-05-01",
                "SANCTION_DATE": "2024-04-01",
                "dqi_score": 1.0,
            }
        ]
    )
    # Negative case: proper sequence
    neg_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "NEG_D4",
                "WORK_ID": "W_NEG_D4",
                "is_retroactive_sanction": False,
                "is_disbursement_before_sanction": False,
                "is_completion_before_sanction": False,
                "RECOMMENDATION_DATE": "2024-04-01",
                "SANCTION_DATE": "2024-05-01",
                "dqi_score": 1.0,
            }
        ]
    )

    assert len(det.detect(pos_row)) == 1
    assert len(det.detect(neg_row)) == 0


def test_archetype_fin_d5_cost_peer_outlier(fitted_baseline_engine):
    """Tests FIN-D5: Cost outlier relative to peer median."""
    det = CostPeerOutlierDetector()
    # Peer median is 505k, IQR is ~25k. 2.5 million is a massive outlier
    pos_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "POS_D5",
                "WORK_ID": "W_POS_D5",
                "STATE_NAME": "DELHI",
                "WORK_CATEGORY": "ROADS",
                "SANCTION_AMOUNT": 2500000.0,
                "dqi_score": 1.0,
            }
        ]
    )
    # Normal cost around 510k
    neg_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "NEG_D5",
                "WORK_ID": "W_NEG_D5",
                "STATE_NAME": "DELHI",
                "WORK_CATEGORY": "ROADS",
                "SANCTION_AMOUNT": 510000.0,
                "dqi_score": 1.0,
            }
        ]
    )

    pos_findings = det.detect(pos_row, baseline_engine=fitted_baseline_engine)
    neg_findings = det.detect(neg_row, baseline_engine=fitted_baseline_engine)

    assert len(pos_findings) == 1
    assert pos_findings[0].detector_code == "FIN-D5"
    assert len(neg_findings) == 0


def test_archetype_fin_d6_cost_overrun():
    """Tests FIN-D6: Total disbursements exceeding sanction amount (>5%)."""
    det = CostOverrunDetector()
    # Positive case: 1.5M disbursed on 1.0M sanction (50% overrun)
    pos_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "POS_D6",
                "WORK_ID": "W_POS_D6",
                "SANCTION_AMOUNT": 1000000.0,
                "total_disbursed": 1500000.0,
                "dqi_score": 1.0,
            }
        ]
    )
    # Negative case: 950k disbursed on 1.0M sanction
    neg_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "NEG_D6",
                "WORK_ID": "W_NEG_D6",
                "SANCTION_AMOUNT": 1000000.0,
                "total_disbursed": 950000.0,
                "dqi_score": 1.0,
            }
        ]
    )

    assert len(det.detect(pos_row)) == 1
    assert len(det.detect(neg_row)) == 0


def test_archetype_exec_d9_progress_mismatch():
    """Tests EXEC-D9: >85% disbursed and >365d elapsed, but not marked complete."""
    det = ProgressExpenditureMismatchDetector()
    # Positive case: 90% disbursed, 400 days, incomplete
    pos_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "POS_D9",
                "WORK_ID": "W_POS_D9",
                "SANCTION_AMOUNT": 1000000.0,
                "total_disbursed": 900000.0,
                "days_since_sanction": 400,
                "ACTUAL_END_DATE": None,
                "dqi_score": 1.0,
            }
        ]
    )
    # Negative case: completed
    neg_row = pd.DataFrame(
        [
            {
                "WORK_RECOMMENDATION_DTL_ID": "NEG_D9",
                "WORK_ID": "W_NEG_D9",
                "SANCTION_AMOUNT": 1000000.0,
                "total_disbursed": 900000.0,
                "days_since_sanction": 400,
                "ACTUAL_END_DATE": "2024-01-01",
                "dqi_score": 1.0,
            }
        ]
    )

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

    random_df = pd.DataFrame(
        {
            "WORK_RECOMMENDATION_DTL_ID": [f"RND_{i}" for i in range(n)],
            "WORK_ID": [f"W_RND_{i}" for i in range(n)],
            "STATE_NAME": np.random.choice(states, n),
            "IDA_NAME": [f"DIST_{i % 5}" for i in range(n)],
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
            "ia_name": [f"AGENCY_{i % 4}" for i in range(n)],
            "primary_vendor": [f"VENDOR_{i % 6}" for i in range(n)],
            "dqi_score": np.random.uniform(0.5, 1.0, n),
        }
    )

    # Execute all detectors
    detectors = [
        SanctionSLABreachDetector(),
        ExecutionDeadlineDetector(),
        StalledDisbursementDetector(),
        LifecycleLeapDetector(),
        CostPeerOutlierDetector(),
        CostOverrunDetector(),
        ProgressExpenditureMismatchDetector(),
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


# ---------------------------------------------------------------------------
# 4. Remediation Verification Tests for Core Detector Issues
# ---------------------------------------------------------------------------


def test_remediation_fin_d5_no_zscore_explosion_on_fixed_tranche():
    """Proves FIN-D5 does not explode to Z > 6000 on tiny variation in fixed-budget cohorts."""
    from dataclasses import dataclass

    @dataclass
    class FixedTrancheBaseline:
        sample_size: int = 100
        cost_median: float = 500000.0
        cost_iqr: float = 1.0  # Artificial compression due to identical fixed tranches
        cost_std: float = 5.0
        cohort_key: tuple = ("DELHI", "Solar")

    class MockEngine:
        def get_peer_baseline(self, state, cat):
            return FixedTrancheBaseline(), 1.0

    # A work with a modest 1% (₹5,000) variation: should NOT be flagged as an outlier
    minor_var_df = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "FIXED_01",
        "STATE_NAME": "DELHI",
        "WORK_CATEGORY": "Solar",
        "SANCTION_AMOUNT": 505000.0,
    }])
    det = CostPeerOutlierDetector(z_threshold=2.5)
    findings = det.detect(minor_var_df, MockEngine())
    assert len(findings) == 0, "Minor 1% variation must not trigger outlier alert on fixed-tranche cohort"

    # A genuine 300% outlier (₹20,00,000 vs ₹5,00,000 median) must be flagged
    major_outlier_df = pd.DataFrame([{
        "WORK_RECOMMENDATION_DTL_ID": "FIXED_02",
        "STATE_NAME": "DELHI",
        "WORK_CATEGORY": "Solar",
        "SANCTION_AMOUNT": 2000000.0,
    }])
    major_findings = det.detect(major_outlier_df, MockEngine())
    assert len(major_findings) == 1
    assert major_findings[0].work_rec_id == "FIXED_02"


def test_remediation_comp_d2_house_normalization_fallback():
    """Proves COMP-D2 properly normalizes house names and applies fallback SLA to unmapped houses."""
    df = pd.DataFrame([
        # Lowercase and space in house name
        {
            "WORK_RECOMMENDATION_DTL_ID": "HOUSE_01",
            "house": "lok sabha",
            "days_sanction_to_completion": 400,  # > 365
            "ACTUAL_END_DATE": pd.Timestamp("2025-06-01"),
            "SANCTION_DATE": pd.Timestamp("2024-04-01"),
        },
        # Null house (fallback to 365 days)
        {
            "WORK_RECOMMENDATION_DTL_ID": "HOUSE_02",
            "house": None,
            "days_since_sanction": 500,  # > 365
            "ACTUAL_END_DATE": pd.NaT,
            "SANCTION_DATE": pd.Timestamp("2024-01-01"),
        },
        # Rajya Sabha tenure exception (540 days): 450 days should NOT breach
        {
            "WORK_RECOMMENDATION_DTL_ID": "HOUSE_03",
            "house": "RAJYA_SABHA",
            "days_since_sanction": 450,  # < 540
            "ACTUAL_END_DATE": pd.NaT,
            "SANCTION_DATE": pd.Timestamp("2024-01-01"),
        },
    ])
    det = ExecutionDeadlineDetector(ls_sla=365, rs_sla=540)
    findings = det.detect(df)
    flagged_ids = {f.work_rec_id for f in findings}
    assert "HOUSE_01" in flagged_ids, "Lok Sabha with space must be flagged when > 365d"
    assert "HOUSE_02" in flagged_ids, "Null house must fallback to standard SLA and be flagged when > 365d"
    assert "HOUSE_03" not in flagged_ids, "Rajya Sabha work at 450d must not breach 540d SLA"


def test_remediation_agy_d11_placeholder_disallowed():
    """Proves AGY-D11 ignores placeholder agency strings ('N/A', 'nan', 'NONE')."""
    from src.engine.detectors.agency import IAOverloadDetector

    records = []
    # 15 delayed works with "N/A" as agency
    for i in range(15):
        records.append({
            "WORK_RECOMMENDATION_DTL_ID": f"NA_{i}",
            "ia_name": "N/A",
            "IDA_NAME": f"DIST_{i}",
            "days_since_sanction": 400,
            "ACTUAL_END_DATE": pd.NaT,
            "total_disbursed": 500000.0,
        })
    df = pd.DataFrame(records)
    det = IAOverloadDetector(min_delayed_works=10, min_total_expenditure=5000000.0)
    findings = det.detect(df)
    assert len(findings) == 0, "'N/A' placeholder must not aggregate into an overloaded super-agency"


def test_remediation_sim_d12_symmetric_emission():
    """Proves SIM-D12 emits reciprocal findings for both works in a duplicate pair."""
    from src.engine.cross_work.similarity import DuplicateWorkDetector

    df = pd.DataFrame([
        {
            "WORK_RECOMMENDATION_DTL_ID": "DUP_A",
            "STATE_NAME": "MAHARASHTRA",
            "IDA_NAME": "PUNE",
            "WORK_CATEGORY": "Water",
            "WORK_DESCRIPTION": "Installation of deep borewell with submersible water pump at village square",
            "SANCTION_AMOUNT": 800000.0,
        },
        {
            "WORK_RECOMMENDATION_DTL_ID": "DUP_B",
            "STATE_NAME": "MAHARASHTRA",
            "IDA_NAME": "PUNE",
            "WORK_CATEGORY": "Water",
            "WORK_DESCRIPTION": "Installation of deep borewell with submersible water pump at village square sector 2",
            "SANCTION_AMOUNT": 810000.0,
        },
    ])
    det = DuplicateWorkDetector(similarity_threshold=0.75, cost_window_ratio=0.20)
    findings = det.detect(df)
    assert len(findings) == 2, "Duplicate detector must emit symmetric findings for both works"
    rec_ids = {f.work_rec_id for f in findings}
    assert rec_ids == {"DUP_A", "DUP_B"}
    # Verify reciprocal cross-referencing
    f_a = next(f for f in findings if f.work_rec_id == "DUP_A")
    f_b = next(f for f in findings if f.work_rec_id == "DUP_B")
    assert f_a.evidence["matched_work_rec_id"] == "DUP_B"
    assert f_b.evidence["matched_work_rec_id"] == "DUP_A"


def test_remediation_rec_d15_fdr_q_values():
    """Proves REC-D15 computes Benjamini-Hochberg FDR q-values in findings evidence."""
    from src.engine.cross_work.recurrence import EntityRecurrenceDetector
    from src.engine.detectors.base import AnomalyCategory

    works = pd.DataFrame([
        {"WORK_RECOMMENDATION_DTL_ID": f"R_{i}", "ia_name": "RECURRING_PWD", "STATE_NAME": "UP"}
        for i in range(5)
    ])
    priors = [
        Finding(
            finding_id=f"F_{i}",
            work_id=f"R_{i}",
            work_rec_id=f"R_{i}",
            detector_code="COMP-D1",
            detector_name="Turnaround",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.8,
            confidence=0.85,
            evidence={},
            explanation="",
            next_review_action="",
        )
        for i in range(5)
    ]
    det = EntityRecurrenceDetector(min_anomalies=3)
    findings = det.detect(works, priors)
    assert len(findings) > 0
    assert "fdr_q_value" in findings[0].evidence
    assert 0.0 <= findings[0].evidence["fdr_q_value"] <= 1.0


def test_remediation_concentration_sorted_by_exposure():
    """Proves AGY-D13 and VND-D14 sort dominant entities' works by financial exposure descending."""
    from src.engine.cross_work.concentration import AgencyConcentrationDetector

    records = []
    # Dominant IA has 16 works (>= 15 threshold) with distinct sanction amounts
    for i in range(16):
        records.append({
            "WORK_RECOMMENDATION_DTL_ID": f"AGY_WORK_{i}",
            "STATE_NAME": "KERALA",
            "IDA_NAME": "KOCHI",
            "ia_name": "MONOPOLY_KERALA_PWD",
            "SANCTION_AMOUNT": float((i + 1) * 100000),  # 100k, 200k, ... 1.6M
        })
    df = pd.DataFrame(records)
    det = AgencyConcentrationDetector(hhi_threshold=2500, share_threshold=0.40)
    findings = det.detect(df)
    # The first sampled finding should be the highest sanction amount (1,600,000)
    assert len(findings) == 5  # Top 5 queue sample
    assert findings[0].work_rec_id == "AGY_WORK_15"
    assert findings[0].sanction_amount == 1600000.0

