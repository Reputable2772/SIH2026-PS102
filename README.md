# SIH PS102 — MPLADS e-SAKSHI Data Mining & Transparency Engine

> **Problem Statement ID:** PS102 (Ministry of Statistics and Programme Implementation - MoSPI)  
> **Scheme:** Members of Parliament Local Area Development Scheme (MPLADS)  
> **Target Portal:** [MPLADS e-SAKSHI Citizen Dashboard](https://www.mplads.mospi.gov.in)

This repository contains the reverse-engineered API specifications, data scrapers, and schema definitions to extract, process, and audit the complete national database of MPLADS developmental projects, fund flows, MP quotas, vendor contracts, and asset lifecycle milestones.

---

## 📑 Table of Contents
1. [Architecture & Reverse Engineering Overview](#architecture--reverse-engineering-overview)
2. [Datasets Available](#datasets-available)
3. [Environment Setup with Nix](#environment-setup-with-nix)
4. [Scraper CLI Usage](#scraper-cli-usage)
5. [Data Linkage & Schema](#data-linkage--schema)
6. [Documentation Directory](#documentation-directory)

---

## 🏛️ Architecture & Reverse Engineering Overview

The official e-SAKSHI portal renders data on a dashboard UI that only aggregates figures by MP. Under the hood, however, the frontend interacts with unauthenticated pre-login REST endpoints that expose **itemized, transaction-level records** for all 36 States/UTs, 543 Lok Sabha constituencies, and 245 Rajya Sabha seats.

### Key API Characteristics:
- **Base URL:** `https://www.mplads.mospi.gov.in`
- **Authentication:** None required (public pre-login REST services).
- **Format:** `POST` with `Content-Type: application/json; charset=utf-8`.
- **Double-Serialized JSON:** Tabular reports return JSON strings inside outer response objects that require two-step parsing.
- **Data Volume:** 81,000+ Sanctioned Works, 109,000+ Recommended Works, 35,000+ Completed Assets, and thousands of vendor disbursement records.

For complete API specifications, endpoint payloads, query combo parameters, and status codes, see [MPLADS_API_DOCUMENTATION.md](scraper/mplads/MPLADS_API_DOCUMENTATION.md).

---

## 📊 Datasets Available

| # | Dataset | API Request Key | Scope / Content |
|---|---|---|---|
| 1 | **Works Recommended** | `Works Recommended` | Full MP project proposals before administrative vetting |
| 2 | **Works Sanctioned** | `Works Sanctioned` | Formally approved community works with financial sanction limits |
| 3 | **Works Completed** | `Works Completed` | Completed assets with handover dates, ratings, and media flags |
| 4 | **Vendor Expenditure** | `Expenditure on Completed and On-going Works as on Date` | Line-item payment vouchers to contractors/vendors with PFMS status |
| 5 | **MP Quota Limits** | `Allocated Limit for Hon'ble MPs` | Statutory entitlement balances & allocations per MP |
| 6 | **Calamity Transfers** | `Amount consented for Calamity` | Voluntary quota donations for national and state disaster relief |
| 7 | **Geographic Master** | `/getStateData`, `/getDistrictByState` | 36 States, 700+ Districts, Constituencies |
| 8 | **Policy Documents** | `/get_fileNames`, `/getFileData` | Official guidelines, user manuals, and permissible work catalogs |

---

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
- Python 3 with `requests` and `pandas`
- `curl` and `jq`
- `nixfmt` code formatter

---

## 🚀 Scraper CLI Usage

The scraper script [`scraper/mplads/mplads_scraper.py`](scraper/mplads/mplads_scraper.py) provides a flexible CLI interface:

### 1. Download Everything (`--all`)
Downloads all 6 core datasets for **both Lok Sabha and Rajya Sabha** across all 36 States/UTs, all geographic hierarchies (states, districts, tenures), and official scheme guideline documents:
```bash
python3 scraper/mplads/mplads_scraper.py --all --output-dir data/mplads_full
```

### 2. Targeted House Extraction
```bash
# Extract Lok Sabha national datasets
python3 scraper/mplads/mplads_scraper.py --house 2 --output-dir data/ls_data

# Extract Rajya Sabha state-by-state datasets
python3 scraper/mplads/mplads_scraper.py --house 1 --output-dir data/rs_data
```

### 3. State-Specific Extraction
```bash
# Extract only Delhi (State ID 11) for Lok Sabha
python3 scraper/mplads/mplads_scraper.py --house 2 --state 11 --output-dir data/delhi
```

### 4. Fetch Master Guidelines & Reference Data Only
```bash
# Download official policy circulars and PDF manuals
python3 scraper/mplads/mplads_scraper.py --documents-only --output-dir docs/guidelines

# Download states and district lookup tables
python3 scraper/mplads/mplads_scraper.py --reference-only --output-dir data/reference
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

Detailed schema definitions, nullability, and JSON samples are documented in [MPLADS_API_DOCUMENTATION.md: Section 3](scraper/mplads/MPLADS_API_DOCUMENTATION.md#3-core-granular-datasets-gettilesreportdata).

---

## 📁 Repository Structure

```
.
├── .envrc                                  # Direnv configuration
├── flake.nix                               # Nix flake definition (Python, devShell, packages)
├── flake.lock                              # Nix flake lockfile
├── README.md                               # Project overview and instructions
└── scraper/
    └── mplads/
        ├── mplads_scraper.py               # Robust CLI bulk scraper with retry and multi-house support
        └── MPLADS_API_DOCUMENTATION.md     # Exhaustive REST API specification & data dictionaries
```
