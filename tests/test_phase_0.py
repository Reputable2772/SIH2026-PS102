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
