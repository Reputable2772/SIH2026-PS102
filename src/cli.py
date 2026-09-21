"""
MPLADS Intelligence Engine — Decoupled Command-Line Interface.

Provides a thin, elegant CLI wrapping the decoupled MPLADSEngine core library.
Usable for data processing, anomaly detection, case dossier inspection, ML training,
validation audits, and interactive HTML report generation.
"""

import argparse
import sys
import json
import webbrowser
from pathlib import Path
import pandas as pd

from src.engine import MPLADSEngine, ReviewPriority
from src.data.pipeline import DataPipeline


def get_engine() -> MPLADSEngine:
    """Initializes the decoupled core analytical engine."""
    return MPLADSEngine()


def maybe_open_browser(filepath: str, requested: bool) -> None:
    """Attempts to launch default browser or google-chrome if requested."""
    if not requested:
        return
    abs_path = Path(filepath).resolve()
    url = f"file://{abs_path}"
    print(f"Opening report in browser: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Note: Could not open browser automatically: {e}")


def cmd_pipeline(args):
    """Executes Phase 0 Data Foundation pipeline."""
    print("=== [PHASE 0] Running MPLADS Data Foundation Pipeline ===")
    pipeline = DataPipeline()
    works, cov = pipeline.run(save_parquet=True)
    print(f"\nSuccessfully reconstructed {len(works):,} canonical works across {len(cov)} state/chamber cohorts.")
    print("\nLifecycle Stage Breakdown:")
    for stage, count in works["lifecycle_stage"].value_counts().items():
        print(f"  - {stage:<15}: {count:>7,} works ({count/len(works):.1%})")


def cmd_detect(args):
    """Runs Phase 1-4 detectors and surfaces ranked review priorities."""
    engine = get_engine()
    sample_size = args.sample

    print(f"=== Running MPLADS Detection & Prioritization Engine (sample: {sample_size or 'all'}) ===")
    results = engine.detect(sample_size=sample_size, include_cross_work=True, include_ml=not args.no_ml)

    print(f"\nAnalyzed {len(results.works):,} works.")
    print(f"Total triggered anomaly findings: {len(results.findings):,}")

    # Review Priorities
    p_summary = results.priority_summary
    print("\nReview Priority Tiers:")
    for prio in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NORMAL"]:
        cnt = p_summary.get(prio, 0)
        pct = cnt / max(len(results.scores), 1)
        print(f"  - {prio:<10}: {cnt:>6,} works ({pct:.1%})")

    # Top cases
    top_cases = results.top_cases(n=args.top)
    print(f"\nTop {len(top_cases)} Prioritized Cases for Human Oversight:")
    print("-" * 95)
    print(f"{'REC ID':<12} | {'STATE':<15} | {'PRIORITY':<8} | {'SEV':<5} | {'CONF':<5} | {'SANCTION (₹)':<12} | {'ANOMALIES'}")
    print("-" * 95)
    for s in top_cases:
        f_codes = [f.detector_code for f in s.findings]
        codes = ",".join(f_codes[:3])
        if len(f_codes) > 3:
            codes += f" (+{len(f_codes)-3})"
        sanc = f"₹{s.sanction_amount:,.0f}" if s.sanction_amount else "N/A"
        print(f"{s.work_rec_id:<12} | {str(s.state_name)[:15]:<15} | {s.priority.value:<8} | {s.composite_severity:<5.2f} | {s.composite_confidence:<5.2f} | {sanc:<12} | {codes}")
    print("-" * 95)
    print("Use `python -m src.cli dossier <WORK_REC_ID>` to inspect any case dossier.")

    # Export options
    if args.export_html:
        out_file = results.export_html(args.export_html)
        print(f"\nExported interactive HTML audit report to: {out_file}")
        maybe_open_browser(out_file, args.open_browser)

    if args.export_json:
        out_file = results.export_json(args.export_json)
        print(f"Exported JSON findings dataset to: {out_file}")


def cmd_dossier(args):
    """Generates the explainable 5-question case dossier for a specific work."""
    rec_id = str(args.work_id)
    engine = get_engine()

    try:
        dossier = engine.generate_dossier(rec_id)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print(f"  AUDIT DOSSIER: WORK REC ID #{dossier.work_rec_id}")
    print(f"  Physical Work ID: {dossier.work_id} | Priority: {dossier.priority}")
    print(f"  State: {dossier.state_name} | District: {dossier.ida_name}")
    print(f"  Sanction Budget: ₹{dossier.sanction_amount:,.0f}")
    print(f"  Severity Score: {dossier.composite_severity:.2f} | Confidence Score: {dossier.composite_confidence:.2f}")
    print("=" * 70)

    print("\n[Q1: WHAT HAPPENED?]")
    print(f"  {dossier.q1_what_happened}")

    print("\n[Q2: WHY IS IT UNUSUAL?]")
    print(f"  {dossier.q2_why_unusual}")

    print("\n[Q3: COMPARED WITH WHAT?]")
    print(f"  {dossier.q3_compared_with_what}")

    print("\n[Q4: SUPPORTING EVIDENCE]")
    for k, v in dossier.q4_supporting_evidence.items():
        print(f"  - {k}: {json.dumps(v, default=str)}")

    print("\n[Q5: LIMITATIONS]")
    print(f"  {dossier.q5_limitations}")

    print("\n[RECOMMENDED NEXT REVIEW ACTIONS (AC-19)]")
    for i, act in enumerate(dossier.next_review_actions, 1):
        print(f"  {i}. {act}")
    print("=" * 70)

    if args.export_html:
        out_file = engine.export_dossier(dossier, format="html", output_path=args.export_html)
        print(f"\nExported interactive case dossier HTML to: {out_file}")
        maybe_open_browser(out_file, args.open_browser)

    if args.export_json:
        out_file = engine.export_dossier(dossier, format="json", output_path=args.export_json)
        print(f"Exported case dossier JSON to: {out_file}")


def cmd_train_ml(args):
    """Trains Phase 4 ML models on real MPLADS data."""
    engine = get_engine()
    sample_size = args.sample

    print(f"=== [PHASE 4] Training ML Models on Real MPLADS Data (sample: {sample_size or 'all'}) ===")
    metadata = engine.train_ml_models(sample_size=sample_size)

    print("\n=== Model Training Complete & Artifacts Persisted ===")
    b_meta = metadata.get("component_b", {})
    print(f"  - Holdout Samples: {b_meta.get('train_samples')} Train / {b_meta.get('test_samples')} Test")
    print(f"  - Class Prevalence: {b_meta.get('class_prevalence', 0):.1%}")
    print(f"  - Holdout AUC-ROC: {b_meta.get('auc_roc', 0):.4f}")
    print(f"  - Holdout PR-AUC: {b_meta.get('pr_auc', 0):.4f}")
    print(f"  - Precision: {b_meta.get('precision', 0):.4f} | Recall: {b_meta.get('recall', 0):.4f}")
    print(f"  - Models saved to: models/anomaly_ensemble.joblib, models/breach_predictor.joblib")


def cmd_validate(args):
    """Runs complete validation suite: injection tests, CAG recall, coverage bias."""
    engine = get_engine()
    print("=== [PHASE 3] Executing Mathematical & Historical Validation Suite ===\n")
    report = engine.run_validation_suite()

    # 1. Monotonicity Injection Test
    mono = report["monotonicity_injection"]
    print("1. Testing Anomaly Injection Monotonicity (AC-13)...")
    print(f"   Status: {mono['status']} (Strictly non-decreasing: {mono['is_monotonic']})")
    print(f"   Tested Delays: {mono['delays_tested']} -> Severities: {[round(s, 2) for s in mono['severities']]}")

    # 2. Cost Sensitivity
    cost = report["cost_sensitivity_injection"]
    print("\n2. Testing Cost Outlier Sensitivity (AC-13)...")
    print(f"   Status: {cost['status']} (FIN-D5 triggered: {cost['has_fin_d5_finding']}, Priority: {cost['outlier_priority']})")

    # 3. Historical CAG Benchmark Recall
    bench = report["historical_cag_benchmark"]
    print("\n3. Testing Historical CAG Report 31 & Parliamentary Q44 Benchmark (AC-16)...")
    print(f"   Status: {bench['status']}")
    print(f"   Empirical Recall: {bench['recall_pct']}% | Precision: {bench['precision_pct']}% | F1: {bench['f1_score']}")
    print(f"   {bench['summary']}")

    # 4. State Coverage-Bias Check
    bias = report["coverage_bias_audit"]
    print("\n4. Testing State Digitization Coverage-Bias Correlation (AC-17)...")
    print(f"   Status: {bias['status']}")
    print(f"   Spearman Rho: {bias['spearman_rho']} (p={bias['p_value']})")
    print(f"   {bias['interpretation']}")

    print(f"\n=== Validation Suite Completed: {report['status']} ===")


def cmd_trends(args):
    """Displays annual macro trends across financial years."""
    engine = get_engine()
    trends = engine.analyze_trends()
    print("=== National MPLADS Operational & Financial Trends (2020-2026) ===")
    print(trends.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(
        prog="mplads-engine",
        description="SIH PS102 — MPLADS e-SAKSHI Autonomous Analytical & Intelligence Core."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available engine commands")

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="Run Phase 0 data normalization & canonical work reconstruction")
    p_pipe.set_defaults(func=cmd_pipeline)

    # detect
    p_det = subparsers.add_parser("detect", help="Run anomaly detection and rank prioritized review cases")
    p_det.add_argument("--sample", type=int, default=10000, help="Number of works to analyze (default: 10000, use 0 for all)")
    p_det.add_argument("--top", type=int, default=15, help="Number of top critical cases to display")
    p_det.add_argument("--no-ml", action="store_true", help="Disable Phase 4 ML integration")
    p_det.add_argument("--export-html", type=str, default=None, help="Export interactive HTML audit dashboard to file")
    p_det.add_argument("--export-json", type=str, default=None, help="Export detection results to JSON file")
    p_det.add_argument("--open-browser", action="store_true", help="Automatically open generated HTML report in browser")
    p_det.set_defaults(func=cmd_detect)

    # dossier
    p_dos = subparsers.add_parser("dossier", help="Generate 5-question explainable audit dossier for a work")
    p_dos.add_argument("work_id", type=str, help="Work recommendation ID (e.g. 101511)")
    p_dos.add_argument("--export-html", type=str, default=None, help="Export case dossier to interactive HTML file")
    p_dos.add_argument("--export-json", type=str, default=None, help="Export case dossier to JSON file")
    p_dos.add_argument("--open-browser", action="store_true", help="Automatically open generated HTML dossier in browser")
    p_dos.set_defaults(func=cmd_dossier)

    # train-ml
    p_ml = subparsers.add_parser("train-ml", help="Train Phase 4 ML models on real data with temporal holdout")
    p_ml.add_argument("--sample", type=int, default=20000, help="Number of works for training (default: 20000)")
    p_ml.set_defaults(func=cmd_train_ml)

    # validate
    p_val = subparsers.add_parser("validate", help="Run validation benchmarks, injection tests, and coverage bias audits")
    p_val.set_defaults(func=cmd_validate)

    # trends
    p_tr = subparsers.add_parser("trends", help="Display macro operational trends over time")
    p_tr.set_defaults(func=cmd_trends)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, "sample") and args.sample == 0:
        args.sample = None

    args.func(args)


if __name__ == "__main__":
    main()
