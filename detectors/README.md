# Prototype Autonomous Core Engine

This directory contains the central brain of the MPLADS anomaly detection pipeline for **SIH Problem Statement 26102**. 

It acts as a headless analytical engine that ingests raw scraper outputs, reconstructs the fragmented lifecycle of government works, and pushes them through a highly rigorous 4-phase detection matrix (combining heuristic rules, statistical baselines, and Machine Learning).

---

## 🏗️ Architecture & Modules

*   **`src/data/` (Phase 0 - Data Foundation)**
    *   **`lifecycle.py`**: The `WorkLifecycleReconstructor` merges Recommendations, Sanctions, Expenditures, and Completions into a single *Canonical Work* object, successfully neutralizing cross-house (Lok Sabha vs Rajya Sabha) primary key collisions.
    *   **`quality.py` & `normalizer.py`**: Enforces strict Data Quality Indices (DQI) and handles "penny drop" transaction filters.

*   **`src/engine/` (Phase 1 to 3 - Detection & Risk)**
    *   **`/detectors/`**: Phase 1 core detectors tracking Financial, Compliance, Agency, and Execution anomalies against dynamical peer baselines (`baselines.py`).
    *   **`/cross_work/`**: Phase 2 systemic intelligence. Detects multi-work fraud like Vendor Monopolies (`VND-D14`), vector-based Semantic Duplication (`SIM-D12`), and Serial Defaulter Recurrence (`REC-D15`) using Empirical Bayes estimators.
    *   **`/risk/`**: Phase 3 composite scoring. Maps 2D severity/confidence vectors onto a unified risk surface and generates human-readable HTML Governance Dossiers.

*   **`src/ml/` (Phase 4 - Artificial Intelligence)**
    *   Trains and evaluates Unsupervised Anomaly Ensembles (Isolation Forests) and Supervised Breach Predictors (XGBoost) without data leakage, integrating AI scores back into the deterministic risk engine.

*   **`src/validation/` (The Audit Simulator)**
    *   Contains the `AnomalyInjectionTester`, which dynamically injects 30 historical fraud archetypes (based on real CAG Audit reports and PQ44 inquiries) into the pipeline to mathematically prove the engine's recall capability.

*   **`tests/`**
    *   A massive, 60+ unit `pytest` suite enforcing mathematical invariants (Subadditivity, Monotonicity) and zero-leakage constraints.

---

## 🎯 The Anomaly Taxonomy

The engine currently executes the following typologies (each uniquely coded for traceability):

| Category | Code | Description |
| :--- | :--- | :--- |
| **Compliance** | `COMP-D1` | Sanction SLA Breach (>45 days) |
| | `COMP-D2` | Execution SLA Breach (>12/18 months) |
| | `COMP-D3` | Stalled Disbursement |
| | `COMP-D4` | Lifecycle Leap (e.g. Disbursement before Sanction) |
| **Financial** | `FIN-D5` | Peer Group Cost Outlier (>2.5 Z-Score against state/category baseline) |
| | `FIN-D6` | Sanction Cost Overrun |
| | `FIN-D8` | Temporal Disbursement Spike ("March Rush" compression) |
| **Execution** | `EXEC-D9` | Progress-Expenditure Mismatch (>85% paid out but stalled for >1 yr) |
| **Agency** | `AGY-D11`| Implementing Agency Capacity Overload |
| **Systemic** | `SIM-D12`| Semantic Vector Duplicate Work Detection |
| | `AGY-D13`| Implementing Agency Concentration |
| | `VND-D14`| Vendor Monopoly Detection (Gini/HHI indices) |
| | `REC-D15`| Serial Defaulter Recurrence |

*(Note: `FIN-D7` and `AGY-D10` are reserved structural codes currently unassigned).*

---

## 🚀 Execution & CLI

The core is decoupled and operates headlessly. To run the full detection pipeline on raw data and generate actionable intelligence reports:

```bash
# Execute the end-to-end pipeline
python3 -m detectors.src.cli run --data-dir ../data/ --output-dir ../reports/ --export-html

# Expected Outputs:
# 1. dossiers.json (Raw JSON for backend consumption)
# 2. audit_report.html (Interactive UI / Human-readable intelligence dossier)
```

## 🛠️ Developer Notes
*   **Robustness:** The core pipeline is hardened against malformed API data (e.g. dirty strings in float columns) via a `safe_float` middleware wrapper.
*   **Tests:** Run `python3 -m pytest detectors/tests/ -v` to verify the mathematical integrity of the engine before deployment.
