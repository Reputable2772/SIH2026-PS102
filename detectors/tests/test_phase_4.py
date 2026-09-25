"""
Test Suite for Phase 4: Machine Learning Training & Integration on Real Data.
"""

import numpy as np
import pandas as pd
import pytest

from src.engine.detectors.base import AnomalyCategory, Finding
from src.ml.anomaly_ensemble import UnsupervisedAnomalyEnsemble
from src.ml.breach_predictor import SupervisedBreachPredictor
from src.ml.features import FeaturePipeline
from src.ml.integration import MLIntegrationManager


@pytest.fixture
def ml_training_corpus():
    """Generates synthetic corpus of 150 works with varying lifecycles and outcomes."""
    np.random.seed(42)
    records = []
    for i in range(150):
        is_delayed = i % 3 == 0
        sanc_date = pd.Timestamp("2023-01-01") + pd.Timedelta(days=i * 3)
        rec_date = sanc_date - pd.Timedelta(days=20 + (50 if is_delayed else 0))
        comp_date = sanc_date + pd.Timedelta(days=450 if is_delayed else 180) if i % 4 != 0 else pd.NaT

        sanc_amt = float(np.random.choice([300000.0, 500000.0, 1000000.0, 2500000.0]))
        disb_amt = sanc_amt if comp_date is not pd.NaT else (sanc_amt * 0.4 if is_delayed else 0.0)

        records.append(
            {
                "WORK_RECOMMENDATION_DTL_ID": f"ML-{i:03d}",
                "WORK_ID": f"WML-{i:03d}",
                "STATE_NAME": np.random.choice(["KERALA", "DELHI", "BIHAR", "GUJARAT"]),
                "WORK_CATEGORY": np.random.choice(["Education", "Roads", "Drinking Water"]),
                "house": "LOK_SABHA",
                "SANCTION_AMOUNT": sanc_amt,
                "RECOMMENDATION_DATE": rec_date,
                "SANCTION_DATE": sanc_date,
                "ACTUAL_END_DATE": comp_date,
                "days_rec_to_sanction": (sanc_date - rec_date).days,
                "days_sanction_to_completion": (comp_date - sanc_date).days if pd.notna(comp_date) else np.nan,
                "days_since_sanction": (pd.Timestamp("2026-01-01") - sanc_date).days,
                "total_disbursed": disb_amt,
                "payment_count": 2 if disb_amt > 0 else 0,
                "days_sanction_to_first_payment": 45,
                "dqi_score": 0.90,
            }
        )
    return pd.DataFrame(records)


def test_feature_pipeline_zero_leakage(ml_training_corpus):
    X, s_map, c_map = FeaturePipeline.build_sanction_time_features(ml_training_corpus)
    # Assert no execution/payment columns leaked
    assert "total_disbursed" not in X.columns
    assert "ACTUAL_END_DATE" not in X.columns
    assert "payment_count" not in X.columns
    assert "days_sanction_to_completion" not in X.columns
    assert len(X) == len(ml_training_corpus)


def test_observation_window_label_builder(ml_training_corpus):
    eligible, labels = FeaturePipeline.construct_breach_labels(ml_training_corpus)
    assert len(eligible) > 0
    assert len(labels) == len(eligible)
    assert set(np.unique(labels)).issubset({0, 1})


def test_unsupervised_anomaly_ensemble(ml_training_corpus):
    ensemble = UnsupervisedAnomalyEnsemble(contamination=0.10)
    ensemble.fit(ml_training_corpus)
    scores = ensemble.predict_anomaly_scores(ml_training_corpus)

    assert len(scores) == len(ml_training_corpus)
    assert all(0.0 <= s <= 1.0 for s in scores)

    findings = ensemble.detect(ml_training_corpus, threshold=0.50)
    assert len(findings) > 0
    f = findings[0]
    assert f.detector_code == "ML-UNSUP-01"
    assert "calibrated_anomaly_score" in f.evidence


def test_supervised_breach_predictor(ml_training_corpus):
    predictor = SupervisedBreachPredictor()
    metrics = predictor.train_and_evaluate(ml_training_corpus)

    assert "auc_roc" in metrics
    assert "precision" in metrics
    assert "confusion_matrix" in metrics
    assert predictor.is_fitted is True

    # Test predicting on in-progress works
    findings = predictor.detect_in_progress_risks(ml_training_corpus, threshold=0.40)
    if findings:
        f = findings[0]
        assert f.detector_code == "ML-BREACH-02"
        assert "predicted_breach_probability" in f.evidence


def test_ml_integration_manager_save_load_score(ml_training_corpus, tmp_path):
    mgr = MLIntegrationManager(models_dir=tmp_path)
    metrics = mgr.train_all(ml_training_corpus)
    assert metrics is not None
    assert (tmp_path / "anomaly_ensemble.joblib").exists()
    assert (tmp_path / "breach_predictor.joblib").exists()
    assert (tmp_path / "ml_metadata.json").exists()

    # Test load
    mgr2 = MLIntegrationManager(models_dir=tmp_path)
    assert mgr2.load_models() is True

    # Generate ML findings
    ml_findings = mgr2.generate_ml_findings(ml_training_corpus)

    # Integrated scoring
    rule_findings = [
        Finding(
            finding_id="F1",
            work_id="ML-001",
            work_rec_id="ML-001",
            detector_code="COMP-D1",
            detector_name="Turnaround",
            category=AnomalyCategory.COMPLIANCE,
            severity=0.8,
            confidence=0.9,
            evidence={},
            explanation="",
            next_review_action="",
        )
    ]
    integrated_scores = mgr2.score_works_integrated(ml_training_corpus, rule_findings, ml_findings)
    assert len(integrated_scores) == len(ml_training_corpus)


def test_supervised_breach_predictor_string_dates(ml_training_corpus):
    """Verifies breach predictor handles string-formatted SANCTION_DATE without quantile subtraction errors."""
    corpus = ml_training_corpus.copy()
    # Convert datetime columns to string/object representation as encountered in CSV loads
    corpus["SANCTION_DATE"] = corpus["SANCTION_DATE"].astype(str)
    if "ACTUAL_END_DATE" in corpus.columns:
        corpus["ACTUAL_END_DATE"] = corpus["ACTUAL_END_DATE"].astype(str)

    predictor = SupervisedBreachPredictor()
    metrics = predictor.train_and_evaluate(corpus)
    assert metrics is not None
    assert predictor.is_fitted is True
