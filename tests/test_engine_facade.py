"""
Tests for decoupled high-level MPLADSEngine coordinator and DetectionResultSet.
Ensures zero coupling between core analytical engine and CLI / UI layers.
"""

import pytest
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from src.engine import MPLADSEngine, DetectionResultSet


@pytest.fixture
def sample_works_df():
    """Provides a synthetic canonical works DataFrame for facade testing."""
    return pd.DataFrame([
        {
            "WORK_RECOMMENDATION_DTL_ID": "REC_001",
            "WORK_ID": "W001",
            "STATE_NAME": "MAHARASHTRA",
            "IDA_NAME": "PUNE",
            "WORK_CATEGORY": "ROADS",
            "WORK_DESCRIPTION": "Construction of asphalt road connecting village sector 4 to main highway",
            "SANCTION_AMOUNT": 1000000.0,
            "total_disbursed": 1200000.0,
            "RECOMMENDATION_DATE": "2023-05-01",
            "SANCTION_DATE": "2023-07-01",  # 61 days > 45d limit -> COMP-D1
            "ACTUAL_END_DATE": None,
            "days_rec_to_sanction": 61,
            "days_since_sanction": 400,
            "days_sanction_to_completion": None,
            "house": "LOK_SABHA",
            "lifecycle_stage": "EXECUTION",
            "ia_name": "PWD_PUNE",
            "primary_vendor": "ROAD_CORP",
            "dqi_score": 0.95
        },
        {
            "WORK_RECOMMENDATION_DTL_ID": "REC_002",
            "WORK_ID": "W002",
            "STATE_NAME": "MAHARASHTRA",
            "IDA_NAME": "PUNE",
            "WORK_CATEGORY": "ROADS",
            "WORK_DESCRIPTION": "Installation of community solar lighting units across public garden",
            "SANCTION_AMOUNT": 500000.0,
            "total_disbursed": 450000.0,
            "RECOMMENDATION_DATE": "2023-05-01",
            "SANCTION_DATE": "2023-05-20",
            "ACTUAL_END_DATE": "2023-11-01",
            "days_rec_to_sanction": 19,
            "days_since_sanction": 500,
            "days_sanction_to_completion": 164,
            "house": "LOK_SABHA",
            "lifecycle_stage": "COMPLETED",
            "ia_name": "PWD_PUNE",
            "primary_vendor": "LOCAL_BUILDERS",
            "dqi_score": 1.0
        }
    ])


def test_engine_detect_decoupled_flow(sample_works_df):
    """Verifies that MPLADSEngine can be initialized and run programmatically without CLI."""
    engine = MPLADSEngine()
    results = engine.detect(works=sample_works_df, include_cross_work=False, include_ml=False)

    assert isinstance(results, DetectionResultSet)
    assert len(results.scores) == 2
    assert isinstance(results.priority_summary, dict)

    # Check top_cases method
    top_cases = results.top_cases(n=5)
    assert len(top_cases) <= 2
    assert top_cases[0].work_rec_id == "REC_001"

    # Check DataFrame export
    df = results.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "work_rec_id" in df.columns
    assert "priority" in df.columns
    assert "next_review_action" in df.columns

    # Check direct dossier retrieval from result set
    dossier_direct = results.get_dossier("REC_001")
    assert dossier_direct.work_rec_id == "REC_001"
    assert len(dossier_direct.next_review_actions) > 0


def test_engine_generate_dossier_and_html(sample_works_df):
    """Verifies that dossier synthesis and HTML export work cleanly."""
    engine = MPLADSEngine()
    dossier = engine.generate_dossier(work_rec_id="REC_001", works=sample_works_df, include_ml=False)

    assert dossier.work_rec_id == "REC_001"
    assert "Statutory limit" in dossier.q3_compared_with_what or "MPLADS" in dossier.q3_compared_with_what
    assert len(dossier.next_review_actions) > 0

    # Test HTML export
    with TemporaryDirectory() as tmpdir:
        html_file = Path(tmpdir) / "test_dossier.html"
        engine.export_dossier(dossier, format="html", output_path=html_file)
        assert html_file.exists()
        content = html_file.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Audit Dossier" in content
        assert "REC_001" in content
        assert "Recommended Next Review Actions" in content


def test_result_set_export_html_and_json(sample_works_df):
    """Verifies exporting DetectionResultSet to HTML and JSON."""
    engine = MPLADSEngine()
    results = engine.detect(works=sample_works_df, include_cross_work=False, include_ml=False)

    with TemporaryDirectory() as tmpdir:
        html_file = Path(tmpdir) / "report.html"
        json_file = Path(tmpdir) / "report.json"

        results.export_html(html_file)
        results.export_json(json_file)

        assert html_file.exists()
        assert json_file.exists()

        html_text = html_file.read_text(encoding="utf-8")
        assert "MPLADS Intelligence Engine" in html_text
        assert "REC_001" in html_text

        json_text = json_file.read_text(encoding="utf-8")
        assert "total_works" in json_text
        assert "priority_summary" in json_text
