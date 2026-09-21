# MPLADS Intelligence Engine — Interactive CLI & Architecture Guide

**System Version:** v0.6.0  
**Problem Statement:** SIH26102 / PS102 (MoSPI - MPLADS e-SAKSHI)  
**Environment:** Nix devShell (`flake.nix`)

---

## 1. Overview & Decoupled Architecture

The **MPLADS Intelligence Engine** is built as a pure, decoupled Python analytical core with an interactive CLI layer:
- **Core Library (`src/`)**: Stateless, modular analytical modules for data processing, rule/statistical detection, network analysis, composite risk scoring, and machine learning. Usable in external scripts, automated workflows, or downstream services (`from src.engine import ...`).
- **CLI Wrapper (`src/cli.py`)**: An interactive command-line interface for running audits, triage review, model training, and validation stress tests.

---

## 2. Environment Setup

Enter the reproducible development shell using Nix:
```bash
# Enter nix devshell
nix develop

# Or run commands directly
nix develop --command python3 -m src.cli --help
```

---

## 3. CLI Command Reference

### 3.1 Data Foundation Pipeline (`pipeline`)
Reconstructs canonical work lifecycles from 15 raw e-SAKSHI datasets across Lok Sabha and Rajya Sabha:
```bash
python3 -m src.cli pipeline
```
*Output:* Normalizes 421,500+ raw records into 101,511 canonical works, calculates Data Quality Indices, and saves `data/processed/canonical_works.parquet`.

### 3.2 Detection & Review Prioritization (`detect`)
Executes all Phase 1 & 2 detectors, scores two-axis risk (Severity and Confidence), and ranks cases for human oversight. Can export interactive HTML audit dashboards:
```bash
# Analyze a sample of 10,000 works and show top 15 critical cases
python3 -m src.cli detect --sample 10000 --top 15

# Export interactive, self-contained HTML audit dashboard & JSON
python3 -m src.cli detect --sample 5000 --html reports/audit_overview.html --json reports/audit_overview.json
```

### 3.3 Explainable Audit Dossier (`dossier`)
Inspects a specific work and generates an audit dossier answering the **5 Core Governance Questions** along with prescribed **Next Review Actions**:
```bash
# CLI text printout
python3 -m src.cli dossier 202625

# Self-contained interactive HTML export with AC-19 checklist
python3 -m src.cli dossier 202625 --html reports/dossier_202625.html --json reports/dossier_202625.json
```
*Governance Output:*
- **Q1 (What happened?):** Timeline delays, expenditure overruns, and milestone stalls.
- **Q2 (Why is it unusual?):** Specific statutory or peer-group deviations.
- **Q3 (Compared with what?):** Statutory 45d/365d limits or state/category peer medians.
- **Q4 (Evidence):** Raw timestamps, voucher amounts, and Z-scores.
- **Q5 (Limitations):** Provenance and confidence bounds.
- **Next Review Actions:** Actionable checklist for district vigilance monitors per AC-19.

### 3.4 Machine Learning Training & Persistence (`train-ml`)
Trains Component A (Isolation Forest) and Component B (Histogram Gradient Boosting early-warning model) on real empirical data using temporal holdout splits:
```bash
python3 -m src.cli train-ml --sample 20000
```
*Output:* Evaluates holdout AUC-ROC, PR-AUC, Precision, Recall, and Confusion Matrix; serializes models to `models/`.

### 3.5 Validation & Quality Assurance (`validate`)
Executes the mathematical stress testing and historical audit validation suite:
```bash
python3 -m src.cli validate
```
*Verifies:*
1. Anomaly injection monotonicity (AC-13).
2. Cost outlier sensitivity (AC-13).
3. Benchmark simulation against CAG Report 31 Chapter 4 & Parliamentary Q44 delay criteria (AC-16).
4. State reporting coverage-bias check (AC-17).

### 3.6 Longitudinal Trend Analysis (`trends`)
Displays macroeconomic operational trends from 2020 to 2026 across sanction volumes, approval delays, and completion rates:
```bash
python3 -m src.cli trends
```

---

## 4. Using the Engine as a Decoupled Python Library

The analytical core is completely decoupled from the CLI. You can import and execute the engine programmatically in any Python application:

```python
from src.engine import MPLADSEngine

# Initialize engine facade
engine = MPLADSEngine()

# 1. Load canonical normalized works
works = engine.load_data(sample_size=5000)

# 2. Run detection across all rule, cross-work, and ML detectors
result = engine.detect(works, include_cross_work=True, include_ml=True)
print(f"Surfaced {len(result.findings)} findings across {len(result.works)} works")
print(result.priority_summary)

# 3. Export interactive HTML dashboard or JSON
result.export_html("reports/audit_overview.html")
result.export_json("reports/audit_overview.json")

# 4. Generate & export individual 5-question audit dossier
dossier = engine.generate_dossier(work_rec_id=202625, works=works)
print(dossier.q1_what_happened)
print(dossier.next_review_actions)
engine.export_dossier(dossier, format="html", output_path="reports/dossier_202625.html")
```

---

## 5. Test Suite Execution

Run the complete 37-test regression and matrix suite:
```bash
nix develop --command pytest tests/ -v
```
- `tests/test_phase_0.py`: Normalization, lifecycle reconstruction, DQI, coverage matrix.
- `tests/test_phase_1.py`: Baselines, compliance (D1-D4), financial (D5-D8), execution (D9), agency (D11).
- `tests/test_phase_2.py`: Duplicate similarity (D12), agency monopolization (D13), vendor capture (D14), recurrence (D15), trends.
- `tests/test_phase_3.py`: Two-axis risk scoring, dossier builder, injection monotonicity, CAG benchmark recall.
- `tests/test_phase_4.py`: Leakage guard, observation window label builder, Isolation Forest, Gradient Boosting, model persistence.
- `tests/test_engine_facade.py`: Decoupled `MPLADSEngine` facade, dataset results, JSON/HTML exports.
- `tests/test_detection_matrix.py`: Complete detection matrix across isolated archetypes, live canonical rows, and 50 randomly mutated synthetic rows.
