"""
Test Suite for Phase 0: Data Foundation & Analytical Model.
"""

import pytest
import pandas as pd
import numpy as np
from src.data.normalizer import DataNormalizer
from src.data.lifecycle import WorkLifecycleReconstructor, LifecycleStage
from src.data.quality import DataQualityAuditor
from src.data.pipeline import DataPipeline


def test_normalizer_dates_and_amounts():
    df = pd.DataFrame({
        "RECOMMENDATION_DATE": ["01-Apr-2025", "invalid", None],
        "SANCTION_AMOUNT": ["500000.0", "-200", "not_a_number"],
        "WORK_DESCRIPTION": ["  Community Hall Construction  ", "None", None],
        "WORK_RECOMMENDATION_DTL_ID": [101.0, 102.0, None]
    })

    norm = DataNormalizer.normalize_dataset(df)

    assert pd.notna(norm["RECOMMENDATION_DATE"].iloc[0])
    assert pd.isna(norm["RECOMMENDATION_DATE"].iloc[1])
    assert norm["SANCTION_AMOUNT"].iloc[0] == 500000.0
    assert norm["SANCTION_AMOUNT"].iloc[1] == 0.0  # Capped negative
    assert norm["SANCTION_AMOUNT"].iloc[2] == 0.0
    assert norm["WORK_DESCRIPTION"].iloc[0] == "Community Hall Construction"
    assert norm["WORK_DESCRIPTION"].iloc[1] is None
    assert norm["WORK_RECOMMENDATION_DTL_ID"].iloc[0] == "101"


def test_work_lifecycle_reconstruction():
    sanc = pd.DataFrame({
        "WORK_RECOMMENDATION_DTL_ID": ["1001"],
        "WORK_ID": ["W1"],
        "SANCTION_DATE": [pd.Timestamp("2025-05-01")],
        "SANCTION_AMOUNT": [1000000.0],
        "STATE_NAME": ["DELHI"],
        "IDA_NAME": ["NORTH DELHI"],
        "WORK_DESCRIPTION": ["School Building Construction"],
        "WORK_CATEGORY": ["Education"]
    })

    rec = pd.DataFrame({
        "WORK_RECOMMENDATION_DTL_ID": ["1001"],
        "RECOMMENDATION_DATE": [pd.Timestamp("2025-04-01")],
        "RECOMMENDED_AMOUNT": [1000000.0]
    })

    exp = pd.DataFrame({
        "WORK_RECOMMENDATION_DTL_ID": ["1001", "1001"],
        "FUND_DISBURSED_AMT": [400000.0, 600000.0],
        "EXPENDITURE_DATE": [pd.Timestamp("2025-06-01"), pd.Timestamp("2025-08-01")],
        "VENDOR_NAME": ["ABC INFRA", "ABC INFRA"],
        "IA_NAME": ["PWD DIVISION 1", "PWD DIVISION 1"],
        "WORK_ID": ["W1", "W1"]
    })

    comp = pd.DataFrame({
        "WORK_RECOMMENDATION_DTL_ID": ["1001"],
        "ACTUAL_AMOUNT": [1000000.0],
        "ACTUAL_END_DATE": [pd.Timestamp("2025-10-01")],
        "WORK_ID": ["W1"]
    })

    reconstructor = WorkLifecycleReconstructor(snapshot_date=pd.Timestamp("2026-01-01"))
    works = reconstructor.reconstruct(rec, sanc, exp, comp, house="LOK_SABHA")

    assert len(works) == 1
    row = works.iloc[0]
    assert row["lifecycle_stage"] == LifecycleStage.COMPLETED
    assert row["days_rec_to_sanction"] == 30
    assert row["days_sanction_to_first_payment"] == 31
    assert row["total_disbursed"] == 1000000.0
    assert row["payment_count"] == 2
    assert row["primary_vendor"] == "ABC INFRA"
    assert row["ia_name"] == "PWD DIVISION 1"


def test_data_quality_index_and_coverage():
    df = pd.DataFrame({
        "WORK_RECOMMENDATION_DTL_ID": ["1001", "1002"],
        "STATE_NAME": ["KERALA", "KERALA"],
        "IDA_NAME": ["ERNAKULAM", "ERNAKULAM"],
        "SANCTION_DATE": [pd.Timestamp("2025-01-01"), pd.NaT],
        "RECOMMENDATION_DATE": [pd.Timestamp("2024-12-01"), pd.NaT],
        "SANCTION_AMOUNT": [500000.0, 0.0],
        "total_disbursed": [500000.0, 0.0],
        "days_rec_to_sanction": [31.0, np.nan],
        "WORK_DESCRIPTION": ["Solar Streetlights across village panchayat", ""],
        "house": ["LOK_SABHA", "LOK_SABHA"],
        "ACTUAL_END_DATE": [pd.Timestamp("2025-06-01"), pd.NaT]
    })

    audited = DataQualityAuditor.compute_work_dqi(df)
    assert "dqi_score" in audited.columns
    assert audited["dqi_score"].iloc[0] > audited["dqi_score"].iloc[1]

    cov = DataQualityAuditor.generate_coverage_matrix(audited)
    assert len(cov) == 1
    assert cov["total_works"].iloc[0] == 2
    assert cov["completion_rate_pct"].iloc[0] == 50.0


def test_payment_status_and_penny_drop_invariants():
    """
    Verifies the 5 Core Frozen Financial Invariants:
    1. Payment Success included in total_disbursed.
    2. Payment In-Progress excluded from total_disbursed (tracked in in_progress_disbursed).
    3. Penny-drop / test transactions (<= 10 INR) excluded from financial analytics.
    4. Missing expenditure remains distinguishable (NaN) from zero confirmed expenditure (0.0).
    5. Downstream financial detectors consume corrected aggregation.
    """
    from src.engine.detectors.compliance import StalledDisbursementDetector
    from src.engine.detectors.financial import CostOverrunDetector

    # Sanctions: Work 101 (mixed vouchers), Work 102 (only in-progress), Work 103 (no vouchers at all)
    sanc = pd.DataFrame({
        "WORK_RECOMMENDATION_DTL_ID": ["101", "102", "103"],
        "WORK_ID": ["W101", "W102", "W103"],
        "SANCTION_DATE": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-01")],
        "SANCTION_AMOUNT": [500000.0, 500000.0, 500000.0],
        "STATE_NAME": ["BIHAR", "BIHAR", "BIHAR"],
        "IDA_NAME": ["PATNA", "PATNA", "PATNA"],
        "WORK_DESCRIPTION": ["Community Center", "Panchayat Hall", "Road Project"],
        "WORK_CATEGORY": ["Community Centers", "Community Centers", "Roads"]
    })

    rec = pd.DataFrame({
        "WORK_RECOMMENDATION_DTL_ID": ["101", "102", "103"],
        "RECOMMENDATION_DATE": [pd.Timestamp("2023-12-01"), pd.Timestamp("2023-12-01"), pd.Timestamp("2023-12-01")],
        "RECOMMENDED_AMOUNT": [500000.0, 500000.0, 500000.0]
    })

    # Work 101 has:
    # - 1 Payment Success voucher: 200,000 INR (genuine)
    # - 1 Payment In-Progress voucher: 150,000 INR (in-progress, must be excluded from total_disbursed)
    # - 1 Penny-drop voucher: 1.0 INR (test transaction, Payment Success, must be excluded from total_disbursed)
    # Work 102 has:
    # - 1 Payment In-Progress voucher: 50,000 INR (all in-progress, so total_disbursed must be 0.0, NOT NaN)
    # Work 103 has NO expenditure records (must have total_disbursed == NaN, NOT 0.0)
    exp = pd.DataFrame({
        "WORK_RECOMMENDATION_DTL_ID": ["101", "101", "101", "102"],
        "FUND_DISBURSED_AMT": [200000.0, 150000.0, 1.0, 50000.0],
        "WORK_STATUS": ["Payment Success", "Payment In-Progress", "Payment Success", "Payment In-Progress"],
        "EXPENDITURE_DATE": [pd.Timestamp("2024-02-01"), pd.Timestamp("2024-03-01"), pd.Timestamp("2024-01-15"), pd.Timestamp("2024-02-01")],
        "VENDOR_NAME": ["M/S ABC", "M/S ABC", "PFMS TEST VENDOR", "M/S XYZ"],
        "IA_NAME": ["RURAL DEV", "RURAL DEV", "RURAL DEV", "RURAL DEV"],
        "WORK_ID": ["W101", "W101", "W101", "W102"]
    })

    comp = pd.DataFrame(columns=["WORK_RECOMMENDATION_DTL_ID", "ACTUAL_AMOUNT", "ACTUAL_END_DATE", "AVERAGE_RATING", "WORK_ID"])

    reconstructor = WorkLifecycleReconstructor(snapshot_date=pd.Timestamp("2024-10-01"))
    works = reconstructor.reconstruct(rec, sanc, exp, comp, house="LOK_SABHA")

    w101 = works[works["WORK_RECOMMENDATION_DTL_ID"] == "101"].iloc[0]
    w102 = works[works["WORK_RECOMMENDATION_DTL_ID"] == "102"].iloc[0]
    w103 = works[works["WORK_RECOMMENDATION_DTL_ID"] == "103"].iloc[0]

    # Invariant 1: Payment Success included
    assert w101["total_disbursed"] == 200000.0
    assert w101["payment_count"] == 1

    # Invariant 2: Payment In-Progress excluded from total_disbursed, available in telemetry
    assert w101["in_progress_disbursed"] == 150000.0
    assert w101["in_progress_payment_count"] == 1

    # Invariant 3: Penny-drop test transactions excluded from total_disbursed
    assert w101["penny_drop_disbursed"] == 1.0
    assert w101["penny_drop_count"] == 1

    # Invariant 4: Distinguishable missing expenditure (NaN) vs zero expenditure (0.0)
    # Work 102 has expenditure records, but 0 succeeded -> total_disbursed == 0.0, has_expenditure_record == True
    assert bool(w102["has_expenditure_record"]) is True
    assert w102["total_disbursed"] == 0.0
    assert w102["in_progress_disbursed"] == 50000.0

    # Work 103 has NO expenditure records -> total_disbursed is NaN, has_expenditure_record == False
    assert bool(w103["has_expenditure_record"]) is False
    assert pd.isna(w103["total_disbursed"])
    assert pd.isna(w103["in_progress_disbursed"])

    # Invariant 5: Downstream financial detectors consume corrected aggregation
    stalled_detector = StalledDisbursementDetector()
    stalled_findings = stalled_detector.detect(works)
    # Both 102 and 103 should be detected as stalled (>90d since sanction, 0 confirmed payments)
    stalled_rec_ids = {f.work_rec_id for f in stalled_findings}
    assert "102" in stalled_rec_ids
    assert "103" in stalled_rec_ids
    assert "101" not in stalled_rec_ids  # 101 had 200k disbursed

    # Verify that evidence distinguishes missing from zero
    f_102 = next(f for f in stalled_findings if f.work_rec_id == "102")
    f_103 = next(f for f in stalled_findings if f.work_rec_id == "103")
    assert f_102.evidence["has_expenditure_record"] is True
    assert f_103.evidence["has_expenditure_record"] is False
    assert f_103.evidence["is_missing_expenditure"] is True

    # CostOverrunDetector must not flag any of these works
    overrun_detector = CostOverrunDetector()
    overrun_findings = overrun_detector.detect(works)
    assert len(overrun_findings) == 0


def test_canonical_identity_uniqueness_and_cross_house_collision_immunity():
    """
    Section 1 Audit Regression Test:
    Proves that WORK_RECOMMENDATION_DTL_ID is globally unique in canonical_works,
    and proves that cross-house collisions are structurally isolated during lifecycle reconstruction.
    """
    from src.config import PROCESSED_DIR
    parquet_path = PROCESSED_DIR / "canonical_works.parquet"
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        # 1. Global uniqueness of WORK_RECOMMENDATION_DTL_ID
        assert df["WORK_RECOMMENDATION_DTL_ID"].nunique() == len(df), (
            f"Collision detected in canonical dataset: {len(df)} rows but {df['WORK_RECOMMENDATION_DTL_ID'].nunique()} unique IDs"
        )
        assert df["WORK_RECOMMENDATION_DTL_ID"].isna().sum() == 0

        # 2. Compound key integrity: (HOUSE_OF_PARLIAMENT, WORK_RECOMMENDATION_DTL_ID, LETTER_NO)
        if "LETTER_NO" in df.columns:
            assert df["LETTER_NO"].isna().sum() == 0
            compound_key = df["house"].astype(str) + "_" + df["WORK_RECOMMENDATION_DTL_ID"].astype(str) + "_" + df["LETTER_NO"].astype(str)
            assert compound_key.nunique() == len(df)

    # 3. Explicit cross-house collision simulation:
    # Prove that even if raw Lok Sabha and Rajya Sabha share identical WORK_RECOMMENDATION_DTL_ID,
    # the per-house lifecycle reconstruction prevents cross-contamination of expenditure/milestones.
    colliding_id = "COLLIDE_9999"
    rec_ls = pd.DataFrame([{"WORK_RECOMMENDATION_DTL_ID": colliding_id, "RECOMMENDATION_DATE": "2024-01-01", "RECOMMENDED_AMOUNT": 500000.0}])
    sanc_ls = pd.DataFrame([{"WORK_RECOMMENDATION_DTL_ID": colliding_id, "SANCTION_DATE": "2024-02-01", "SANCTION_AMOUNT": 500000.0, "WORK_ID": "W_LS", "STATE_NAME": "BIHAR", "IDA_NAME": "PATNA"}])
    exp_ls = pd.DataFrame([{"WORK_RECOMMENDATION_DTL_ID": colliding_id, "FUND_DISBURSED_AMT": 500000.0, "WORK_STATUS": "Payment Success", "EXPENDITURE_DATE": "2024-03-01", "VENDOR_NAME": "LS_VENDOR", "IA_NAME": "LS_IA", "WORK_ID": "W_LS"}])
    comp_cols = ["WORK_RECOMMENDATION_DTL_ID", "ACTUAL_AMOUNT", "ACTUAL_END_DATE", "AVERAGE_RATING", "WORK_ID"]
    comp_ls = pd.DataFrame(columns=comp_cols)

    rec_rs = pd.DataFrame([{"WORK_RECOMMENDATION_DTL_ID": colliding_id, "RECOMMENDATION_DATE": "2024-05-01", "RECOMMENDED_AMOUNT": 1000000.0}])
    sanc_rs = pd.DataFrame([{"WORK_RECOMMENDATION_DTL_ID": colliding_id, "SANCTION_DATE": "2024-06-01", "SANCTION_AMOUNT": 1000000.0, "WORK_ID": "W_RS", "STATE_NAME": "KERALA", "IDA_NAME": "KOCHI"}])
    exp_rs = pd.DataFrame([{"WORK_RECOMMENDATION_DTL_ID": colliding_id, "FUND_DISBURSED_AMT": 200000.0, "WORK_STATUS": "Payment Success", "EXPENDITURE_DATE": "2024-07-01", "VENDOR_NAME": "RS_VENDOR", "IA_NAME": "RS_IA", "WORK_ID": "W_RS"}])
    comp_rs = pd.DataFrame(columns=comp_cols)

    reconstructor = WorkLifecycleReconstructor()
    works_ls = reconstructor.reconstruct(rec_ls, sanc_ls, exp_ls, comp_ls, house="LOK_SABHA")
    works_rs = reconstructor.reconstruct(rec_rs, sanc_rs, exp_rs, comp_rs, house="RAJYA_SABHA")

    # Verify per-house isolation
    assert works_ls.iloc[0]["house"] == "LOK_SABHA"
    assert works_ls.iloc[0]["total_disbursed"] == 500000.0
    assert works_ls.iloc[0]["primary_vendor"] == "LS_VENDOR"

    assert works_rs.iloc[0]["house"] == "RAJYA_SABHA"
    assert works_rs.iloc[0]["total_disbursed"] == 200000.0
    assert works_rs.iloc[0]["primary_vendor"] == "RS_VENDOR"

    # When concatenated into national corpus, compound key disambiguates them perfectly
    combined = pd.concat([works_ls, works_rs], ignore_index=True)
    compound_keys = combined["house"] + "_" + combined["WORK_RECOMMENDATION_DTL_ID"]
    assert compound_keys.nunique() == 2


def test_longitudinal_pre_2023_boundary_isolation():
    """
    Section 6 Audit Regression Test:
    Verifies that canonical e-SAKSHI works represent post-April 1, 2023 mandatory digital coverage,
    and ensures pre-2023 historical records cannot be silently mixed into e-SAKSHI digital benchmarks.
    """
    from src.config import PROCESSED_DIR
    parquet_path = PROCESSED_DIR / "canonical_works.parquet"
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        sanc_dates = pd.to_datetime(df["SANCTION_DATE"], errors="coerce")
        cutoff = pd.Timestamp("2023-04-01")
        # In current canonical data, 100% of sanctions are post-April 1, 2023
        pre_count = (sanc_dates < cutoff).sum()
        assert pre_count == 0, f"Found {pre_count} pre-April 2023 records in canonical digital dataset"
