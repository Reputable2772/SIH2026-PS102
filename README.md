# SIH PS102 — MPLADS e-SAKSHI Data Mining & Transparency Engine

> **Problem Statement ID:** PS102 (Ministry of Statistics and Programme Implementation - MoSPI)  
> **Scheme:** Members of Parliament Local Area Development Scheme (MPLADS)  
> **Target Portal:** [MPLADS e-SAKSHI Citizen Dashboard](https://www.mplads.mospi.gov.in)

This repository contains the reverse-engineered API specifications, data scrapers, and schema definitions to extract, process, and audit the complete national database of MPLADS developmental projects, fund flows, MP quotas, vendor contracts, and asset lifecycle milestones.

---

## 📑 Table of Contents
1. [Architecture & Reverse Engineering Overview](#architecture--reverse-engineering-overview)
2. [Datasets Available & Data Architecture](#-phase-0-data-architecture-primary-scrape-vs-supplementary-evidence)
3. [Environment Setup with Nix](#-environment-setup-with-nix)
4. [Intelligence Engine CLI Usage](#-intelligence-engine-cli-usage)
5. [Scraper CLI Usage](#-scraper-cli-usage)
6. [Using the Engine as a Python Library](#-using-the-engine-as-a-python-library)
7. [Running the Test Suite](#-running-the-test-suite)
8. [Data Linkage & Schema](#-data-linkage--schema)
9. [Repository Structure](#-repository-structure)
10. [Documentation Directory](#-documentation-directory)

---

## 🏛️ Architecture & Reverse Engineering Overview

The official e-SAKSHI portal renders data on a dashboard UI that only aggregates figures by MP. Under the hood, however, the frontend interacts with unauthenticated pre-login REST endpoints that expose **itemized, transaction-level records** for all 36 States/UTs, 543 Lok Sabha constituencies, and 245 Rajya Sabha seats.

### Key API Characteristics:
- **Base URL:** `https://www.mplads.mospi.gov.in`
- **Authentication:** None required (public pre-login REST services).
- **Format:** `POST` with `Content-Type: application/json; charset=utf-8`.
- **Double-Serialized JSON:** Tabular reports return JSON strings inside outer response objects that require two-step parsing.
- **Data Volume:** 101,511 Sanctioned Works, 135,078 Recommended Works, 45,704 Completed Assets, and 111,935 vendor disbursement records (395,871 total rows across 15 datasets).

For complete API specifications, endpoint payloads, query combo parameters, and status codes, see [MPLADS_API_DOCUMENTATION.md](scraper/mplads/MPLADS_API_DOCUMENTATION.md).

---

## 📊 Phase 0 Data Architecture: Primary Scrape vs. Supplementary Evidence

To ensure the prototype maintains a rigorous boundary between operational pipeline data and external validation benchmarks, Phase 0 sources are frozen into two distinct tiers:

### Tier 1: Primary Input Datasets (First-Party e-SAKSHI Public REST API)
These form the 395,000+ record empirical core extracted directly from first-party e-SAKSHI endpoints (395,871 total rows across 15 CSV files):

| Dataset | API Key / Endpoint | Records | Scope & Content |
|---|---|---|---|
| **Works Recommended** | `Works Recommended` | 135,078 | Complete itemized project proposals from Lok Sabha & Rajya Sabha MPs |
| **Works Sanctioned** | `Works Sanctioned` | 101,511 | Formally approved works with administrative and financial sanction |
| **Works Completed** | `Works Completed` | 45,704 | Completed physical community assets with handover sign-offs |
| **Vendor Expenditure** | `Expenditure on Completed...` | 111,935 | Line-item payment vouchers disbursed to contractors and executing agencies |
| **MP Quota Limits** | `Allocated Limit for Hon'ble MPs`| 775 | Statutory entitlement balances & allocations per MP |
| **Calamity Transfers** | `Amount consented for Calamity` | 32 | Quota surrendered by MPs for disaster relief |
| **Geographic Master** | `/getStateData`, `/getDistrictByState` | 36 States, 796 Dists | Administrative translation tables |
| **Tenure Master** | `/getTenureData` | 4 Tenures | Parliamentary term codes |

### Tier 2: Supplementary Validation Evidence (Benchmarks & Audit Typologies)
These sources provide external validation benchmarks, statutory operational thresholds, and ground-truth audit typologies without adding complex, un-joinable schemas into the primary pipeline:

| Validation Source | Provenance & Document | Role in Prototype |
|---|---|---|
| **MoSPI Annual Reports** | MoSPI Annual Report 2023–24 | Scheme-level historical sanity checks (validating scraped aggregates against official published totals) |
| **Parliamentary Q&A Annexures** | Lok Sabha Unstarred Question AU4517 | External official benchmarks for state/year-wise allocation, release, utilization, and average sanction turnaround |
| **Parliamentary e-SAKSHI Monitoring Framework** | 18th Lok Sabha Standing Committee on Finance (Report 35) | Defines official operational delay criteria: **>45 days pending sanction**, **>1 year incomplete after sanction**, **>3 months without payment** |
| **Parliamentary Impact & Evaluation Material** | Lok Sabha Question AU3350 Annexure | 216-district evaluation covering 2014–2019 that informed the 2023 revised guidelines |
| **CAG Performance Audits on MPLADS** | CAG Union Performance Audit (Report 31 of 2010, Chapter 4) | Ground-truth audit validation corpus documenting real-world ghost assets, post-completion disbursements, and procurement irregularities |
| **Scheme Guidelines & Circulars** | MPLADS Guidelines w.e.f. 1 April 2023 & Annexure-VIII | Official permissible work catalog, tender ceilings, and administrative SOPs |

### Setup for Supplementary Validation Files:
Supplementary validation documents are stored locally under `data/validation_evidence/` and `data/official_documents/`.
> [!NOTE]
> Ensure parent directories are created with `--create-dirs` (or `mkdir -p data/validation_evidence`) to prevent curl write errors.

```bash
# MoSPI Annual Report 2023-24 (18 MB)
curl -k -sS -L --create-dirs "https://mospi.gov.in/sites/default/files/publication_reports/AnnualReport_2023-24.pdf" \
  -o "data/validation_evidence/mospi_annual_report_2023_24.pdf"

# CAG Performance Audit on MPLADS Works (2.6 MB)
curl -k -sS -L --create-dirs "https://cag.gov.in/webroot/uploads/download_audit_report/2010/Union_Performance_Local_area_Development_Scheme_31_2010_chapter_4.pdf" \
  -o "data/validation_evidence/cag_mplads_audit_ch4.pdf"
```

> **How Supplementary Validation Files Are Used:**  
> These PDFs serve as external qualitative benchmarks, sanity checks, and statutory ground truth. Rather than running slow/unreliable PDF ingestion in the real-time pipeline, their statutory criteria (e.g. 45-day sanction SLA, 365-day execution deadline, 90-day disbursement stall) are codified into [`detectors/src/config.py`](detectors/src/config.py), and their documented audit typologies (such as CAG Report 31 dormancy and Parliamentary Q44 breaches) are codified into [`detectors/src/validation/benchmark.py`](detectors/src/validation/benchmark.py) to mathematically benchmark and test detection recall.

### Public Work-Level Endpoint Investigation:
An exhaustive probe of e-SAKSHI routes confirmed the following work-level endpoints:
- **Attachment List:** `POST /rest/PreLoginDashboardData/getAttachIdsbyFlag` with `{"json": {"FLAG": 3, "WORK_ID": <ID>}}` returns file names and composite attachment IDs (e.g. `1836498.1905867`).
- **Attachment Content:** `POST /rest/PreLoginCitizenWorkRcmdRest/getAttachmentById` with `{"id": "<ATTACH_ID>"}` returns complete base64-encoded PDF completion certificates and JPEG inspection photos without authentication.
- **Citizen Reviews:** `POST /rest/PreLoginCitizenWorkRcmdRest/getReviewDetailsByWork` returns public star ratings and reviews.
- **Unavailable / Private Endpoints:** Candidate routes for raw GIS coordinates (`/getGisData`) and interim progress tracking (`/getWorkDetails`, `/getWorkProgress`) return `404 Not Found`; they are not publicly exposed outside privileged authenticated sessions.

## ⚡ Environment Setup with Nix

This repository uses [Nix flakes](flake.nix) to guarantee an identical, reproducible development environment across Linux and macOS.

### Quick Start with `direnv`:
```bash
# Allow direnv to auto-load the environment
direnv allow
```

### Or using standard Nix:
```bash
# Enter the nix devshell
nix develop

# Or run commands directly
nix develop --command python3 scraper/mplads/mplads_scraper.py --help
```

The shell provides:
- Python 3 with `requests`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `pyarrow`, `jinja2`, `joblib`, and `pytest`
- `curl`, `jq`, and `ruff`
- `nixfmt` code formatter

---

## 🚀 Scraper CLI Usage

The scraper script [`scraper/mplads/mplads_scraper.py`](scraper/mplads/mplads_scraper.py) provides a flexible CLI interface:

### 1. Download Everything (`--all`)
Downloads all 6 core datasets for **both Lok Sabha and Rajya Sabha** across all 36 States/UTs, all geographic hierarchies (states, districts, tenures), and official scheme guideline documents:
```bash
python3 scraper/mplads/mplads_scraper.py --all --out-dir data
```

### 2. Targeted House Extraction
```bash
# Extract Lok Sabha national datasets
python3 scraper/mplads/mplads_scraper.py --house lok_sabha --dataset completed --out-dir data

# Extract Rajya Sabha state-by-state datasets
python3 scraper/mplads/mplads_scraper.py --house rajya_sabha --dataset completed --out-dir data
```

### 3. State-Specific Extraction
```bash
# Extract only Delhi (State ID 11) for Lok Sabha
python3 scraper/mplads/mplads_scraper.py --house lok_sabha --state 11 --out-dir data/delhi
```

### 4. Skip Downloading PDFs During Bulk Scrape
```bash
# Download all datasets while skipping guideline PDF downloads
python3 scraper/mplads/mplads_scraper.py --all --skip-docs --out-dir data
```

---

## 🔗 Data Linkage & Schema

The datasets form a relational schema interconnected via primary and foreign keys:

```
[MP Allocation Quota]
        │
        ▼ (Allocated Limit)
[Works Recommended] ─── WORK_RECOMMENDATION_DTL_ID ───► [Works Sanctioned]
                                                               │
                                         ┌─────────────────────┴─────────────────────┐
                                         ▼ (WORK_ID)                                 ▼ (WORK_ID)
                                 [Expenditure / Vendors]                    [Works Completed]
                                                                                     │
                                                                                     ▼ (ATTACH_ID)
                                                                           [Inspection Photos / PDFs]
```

Detailed schema definitions, nullability, and JSON samples are documented in [MPLADS_API_DOCUMENTATION.md: Section 3](scraper/mplads/MPLADS_API_DOCUMENTATION.md#3-core-granular-datasets-gettilesreportdata). Complete empirical join audits and data quality findings are in [phase_0_data_foundation.md](docs/phase_0_data_foundation.md).

---

## 🧠 Intelligence Engine CLI Usage

The analytical core provides an interactive CLI ([`detectors/src/cli.py`](detectors/src/cli.py)) and Nix application (`nix run .#mplads-engine -- ...`):

```bash
# Reconstruct canonical work lifecycles from 15 raw datasets
python3 -m detectors.src.cli pipeline
# or: nix run .#mplads-engine -- pipeline

# Run multi-detector anomaly scan & rank critical review cases
python3 -m detectors.src.cli detect --sample 10000 --top 15

# Export interactive, self-contained HTML audit dashboard & JSON report
python3 -m detectors.src.cli detect --sample 5000 --html reports/audit_overview.html --json reports/audit_overview.json

# Generate an Explainable 5-Question Audit Dossier for an individual work
python3 -m detectors.src.cli dossier 202625 --html reports/dossier_202625.html

# Train unsupervised (Isolation Forest) & supervised early-warning models
python3 -m detectors.src.cli train-ml --sample 20000

# Execute mathematical validation suite (Monotonicity, CAG Recall, Coverage Bias)
python3 -m detectors.src.cli validate

# Analyze macroeconomic operational trends across tenures
python3 -m detectors.src.cli trends
```

For complete CLI flags and options, see the comprehensive [User Guide](docs/USER_GUIDE.md).

---

## 💻 Using the Engine as a Python Library

The analytical core is decoupled from the CLI and can be embedded directly into custom workflows:

```python
from detectors import MPLADSEngine

engine = MPLADSEngine()

# Load canonical normalized works
works = engine.load_data(sample_size=5000)

# Run detection across rule-based, cross-work, and ML detectors
result = engine.detect(works, include_cross_work=True, include_ml=True)
print(f"Flagged {len(result.findings)} findings across {len(result.works)} works")

# Export audit report or inspection dossier
result.export_html("reports/audit_overview.html")
dossier = engine.generate_dossier(work_rec_id=202625, works=works)
engine.export_dossier(dossier, format="html", output_path="reports/dossier_202625.html")
```

---

## 🧪 Running the Test Suite

Run the full 59-test automated regression and detection matrix suite:
```bash
nix develop --command pytest -v
# or simply:
pytest -v
```

---

## 📁 Repository Structure

```
.
├── .envrc                                      # Direnv environment auto-load
├── flake.nix                                   # Reproducible Nix flake definition
├── flake.lock                                  # Locked Nix dependencies
├── pyproject.toml                              # Ruff formatting and linting configuration
├── pytest.ini                                  # Pytest configuration
├── README.md                                   # Project overview and quickstart
├── docs/
│   ├── USER_GUIDE.md                           # Interactive CLI & Architecture User Guide
│   ├── Core.md                                 # Core prototype specification & implementation guide
│   ├── phase_0_data_foundation.md              # Canonical Phase 0 data audit & schema specification
│   ├── phase_1_baselines_and_core_detection.md # Phase 1 baselines & core rule detectors
│   ├── phase_2_cross_work_and_pattern_intelligence.md # Network & similarity detectors
│   ├── phase_3_risk_explainability_and_validation.md  # Two-axis risk scoring & validation suite
│   └── phase_4_ml_models_and_integration.md    # Machine learning ensemble & pipeline integration
├── detectors/
│   ├── __init__.py                             # Package exports (MPLADSEngine, DetectionResultSet)
│   ├── src/
│   │   ├── cli.py                              # Unified interactive CLI entrypoint
│   │   ├── config.py                           # Statutory policy thresholds & baseline configuration
│   │   ├── data/                               # Ingestion, normalization & lifecycle reconstruction
│   │   ├── engine/                             # Rule detectors, risk scorer & engine facade
│   │   ├── ml/                                 # Isolation Forest & Gradient Boosting early-warning models
│   │   └── validation/                         # Anomaly injection, CAG benchmarks & coverage bias
│   └── tests/                                  # Full 59-test automated regression & matrix test suite
└── scraper/
    └── mplads/
        ├── mplads_scraper.py                   # High-resilience REST bulk scraper
        └── MPLADS_API_DOCUMENTATION.md         # Exhaustive REST API specification
```

---

## 📚 Documentation Directory

- [Interactive CLI & Architecture User Guide](docs/USER_GUIDE.md)
- [Core Prototype Specification](docs/Core.md)
- [Phase 0: Canonical Data Foundation](docs/phase_0_data_foundation.md)
- [Phase 1: Baselines & Core Anomaly Detection](docs/phase_1_baselines_and_core_detection.md)
- [Phase 2: Cross-Work & Pattern Intelligence](docs/phase_2_cross_work_and_pattern_intelligence.md)
- [Phase 3: Two-Axis Risk & Validation Suite](docs/phase_3_risk_explainability_and_validation.md)
- [Phase 4: ML Models & Pipeline Integration](docs/phase_4_ml_models_and_integration.md)
- [e-SAKSHI REST API Documentation](scraper/mplads/MPLADS_API_DOCUMENTATION.md)
