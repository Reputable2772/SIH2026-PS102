# Phase 0 — Data Foundation & Canonical Analytical Specification
**MPLADS Intelligence Engine (SIH PS102)**  
**Authoritative Snapshot:** 2026-09-21  
**Target Portal:** [MPLADS e-SAKSHI Citizen Dashboard](https://www.mplads.mospi.gov.in)  
**Document Status:** Canonical Phase 0 Specification (Unified Data Audit & Analytical Domain Model)  
**Architecture Mapping:** Phase 0 of 4-Phase System Architecture ([`Core.md`](Core.md))

---

## 1. Executive Summary & Phase 0 Mandate

### 1.1 Purpose and Architectural Role
Under the 4-Phase Architecture defined in [`Core.md`](Core.md), **Phase 0 (Data Foundation & Analytical Model)** establishes the empirical reality, canonical domain representations, and data-governance invariants for the MPLADS Intelligence Engine. 

This document unifies:
1. **The Empirical Data Audit:** Exhaustive accounting, nullability profiling, duplicate validation, and official reconciliation of all scraped first-party e-SAKSHI datasets.
2. **The Canonical Domain Model:** Rigorous entity-relationship specifications, multi-tier work identity hierarchies, financial aggregation invariants, and deterministic missing-data handling rules.
3. **Detector Feasibility & Scope Freeze:** An evidence-backed feasibility taxonomy (GREEN / YELLOW / RED) bounding what anomaly detectors the prototype can legitimately implement without inventing unsupported fields or drawing speculative institutional inferences.

### 1.2 Core Architectural Invariants & Governance Principles
All downstream development across Phase 1 (Core Baselines & Detectors), Phase 2 (Cross-Work & Pattern Intelligence), and Phase 3 (Risk Profiling & Validation) must strictly conform to these five foundational constraints:

1. **Specification Only (Zero Implementation in Phase 0):** Phase 0 defines entities, keys, relations, and analytical rules. No implementation code for detectors, ML models, REST APIs, frontend interfaces, or databases is introduced here.
2. **Strict Rule Against Field Invention:** The analytical engine operates exclusively on observed portal fields. No unobserved attributes—such as GPS coordinates, intermediate physical construction percentages, competitive tender bids, or demographic SC/ST census mappings—may be synthesized or assumed.
3. **Empirical Groundedness & Provenance:** Every metric, key, and capability is grounded in observed first-party data structures extracted directly from the official e-SAKSHI portal.
4. **Epistemic Discipline (Observation vs. Inference):** The engine audits administrative portal records, not on-site physical construction reality. Discrepancies represent administrative anomalies warranting review, never legal determinations of fraud, corruption, or intentional criminality.
5. **Preservation of Raw Data Immutability:** The raw scraped datasets in `data/` are immutable historical snapshots (395,871 CSV rows across 15 files). Cleaning, normalization, and relational key resolution occur strictly in downstream analytical staging layers without mutating source files.

---

# Part I: Empirical Data Audit & Integrity Verification

## 2. Complete First-Party Dataset Inventory

The raw dataset comprises **395,871 rows across 15 CSV files** (totaling ~101.4 MB on disk), scraped directly from the official e-SAKSHI portal API endpoints. The corpus partitions into 12 granular work and expenditure lifecycle datasets (395,035 rows) and 3 master geographic reference ledgers (836 rows):

| Dataset File Name | Chamber / Scope | Milestone / Function | Row Count | File Size (Bytes) | Operational Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `mplads_lok_sabha_recommended.csv` | Lok Sabha | Recommendation | **109,412** | 33,354,821 | Project proposals submitted by Lok Sabha MPs. |
| `mplads_lok_sabha_sanctioned.csv` | Lok Sabha | Administrative Sanction | **81,466** | 22,668,791 | Works sanctioned by District Authorities. |
| `mplads_lok_sabha_completed.csv` | Lok Sabha | Completion Milestone | **35,557** | 8,970,302 | Assets formally certified as completed. |
| `mplads_lok_sabha_expenditures.csv` | Lok Sabha | Financial Disbursements | **89,715** | 18,367,294 | Itemized commercial vendor payment vouchers. |
| `mplads_rajya_sabha_recommended.csv` | Rajya Sabha | Recommendation | **25,666** | 7,657,328 | Project proposals submitted by Rajya Sabha MPs. |
| `mplads_rajya_sabha_sanctioned.csv` | Rajya Sabha | Administrative Sanction | **20,045** | 5,496,259 | Works sanctioned by District Authorities. |
| `mplads_rajya_sabha_completed.csv` | Rajya Sabha | Completion Milestone | **10,147** | 2,525,005 | Assets formally certified as completed. |
| `mplads_rajya_sabha_expenditures.csv`| Rajya Sabha | Financial Disbursements | **22,220** | 4,505,078 | Itemized commercial vendor payment vouchers. |
| `mplads_lok_sabha_allocations.csv` | Lok Sabha | Financial Ceiling | **543** | 72,504 | Constituency entitlement ledgers. |
| `mplads_rajya_sabha_allocations.csv` | Rajya Sabha | Financial Ceiling | **232** | 30,739 | State/Nominated entitlement ledgers. |
| `mplads_lok_sabha_calamity.csv` | Lok Sabha | Emergency Release | **14** | 2,875 | Disaster consent allocations. |
| `mplads_rajya_sabha_calamity.csv` | Rajya Sabha | Emergency Release | **18** | 3,745 | Disaster consent allocations. |
| `mplads_master_states.csv` | National | Master Geographic | **36** | 1,489 | Master register of States and UTs. |
| `mplads_master_districts.csv` | National | Master Geographic | **257** | 13,836 | Master district authority mapping. |
| `mplads_master_constituencies.csv` | National | Master Geographic | **543** | 27,249 | Master Lok Sabha parliamentary constituencies. |
| **Total Comprehensive Scope** | — | — | **395,871** | **103,697,315** | **Exhaustive national corpus across both houses.** |

### 2.1 System Reconciliations against Official Dashboard Counters
The scraped dataset was reconciled against official dashboard summary counters exposed by the e-SAKSHI portal (`data/scheme_cumulative_totals.json`):

| Analytical Stage Metric | Scraped Dataset Count | e-SAKSHI Dashboard Counter | Reconciliation Difference | Integrity Verification Finding |
| :--- | :--- | :--- | :--- | :--- |
| **Total Recommended Works** | **135,078** (109,412 LS + 25,666 RS) | **135,078** | **0 (0.00%)** | **Reconciled exactly** with official dashboard counters. |
| **Total Sanctioned Works** | **101,511** (81,466 LS + 20,045 RS) | **101,511** | **0 (0.00%)** | **Reconciled exactly** with official dashboard counters. |
| **Total Completed Works** | **45,704** (35,557 LS + 10,147 RS) | **45,704** | **0 (0.00%)** | **Reconciled exactly** with official dashboard counters. |
| **Disbursement Transactions**| **111,935** (89,715 LS + 22,220 RS) | **111,935** | **0 (0.00%)** | **Reconciled exactly** across all payment tranches. |

---

## 3. Field-Level Data Dictionary & Nullability

This section establishes the definitive schema, data types, nullability rates, and semantic definitions for all observed portal fields across the 15 raw datasets:

### 3.1 Works Recommended (`FLAG = 1`)
- **Source Datasets:** `mplads_lok_sabha_recommended.csv` (109,412 rows), `mplads_rajya_sabha_recommended.csv` (25,666 rows)

| Column Name | Inferred Dtype | Null Count (Rate %) | Example Values | Semantic Role | Analytical Definition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Sno` | `int64` | 0 (0.00%) | `1`, `2`, `3` | Presentation | Display row number from web table. |
| `HOUSE_OF_PARLIAMENT` | `str` | 0 (0.00%) | `LOK_SABHA`, `RAJYA_SABHA` | Chamber Partition | Parliamentary body governing MP's seat. |
| `WORK_RECOMMENDATION_DTL_ID`| `int64` | 0 (0.00%) | `18398`, `192454` | **Source Sequence Key** | Primary internal surrogate sequence ID for the recommendation event. |
| `LETTER_NO` | `str` | 0 (0.00%) | `01/MP/2024`, `Letter-99` | **Disambiguator** | MP's official dispatch letter reference number. Disambiguates legacy collisions. |
| `RECOMMENDATION_DATE` | `str` (Date) | 0 (0.00%) | `15-Jul-2024`, `02-Jan-2025` | **Temporal Benchmark** | Date work was officially submitted. Format: `DD-Mon-YYYY`. |
| `RECOMMENDED_AMOUNT` | `float64` | 0 (0.00%) | `500000.0`, `1250000.0` | **Financial Benchmark** | Cost estimate proposed by MP in Indian Rupees (₹). |
| `WORK_STAGE` | `str` | LS: 574 (0.52%), RS: 112 (0.44%) | `Pending for Sanction`, `Sanction` | Workflow State | Point-in-time administrative status string. |
| `ACTIVITY_NAME` | `str` | 0 (0.00%) | `WS/MP18398/2026-2027/243454` | Descriptive String | Structured identifier containing sequence ID in modern records. |
| `WORK_CATEGORY` | `str` | 0 (0.00%) | `Normal/Others`, `Repair and Renovation` | Policy Category | Broad administrative sector classification. |
| `WORK_DESCRIPTION` | `str` | LS: 114 (0.10%), RS: 0 (0.00%) | `Construction of CC Road...` | Textual Specification | Detailed scope of work entered by MP office. |
| `STATE_NAME` | `str` | 0 (0.00%) | `Uttar Pradesh`, `Maharashtra` | Geography | State or Union Territory of project site. |
| `CONSTITUENCY_ID` | `int64` | 0 (0.00%) | `182`, `545`, `546` | Administrative ID | Parliamentary constituency identifier code. |
| `CONSTITUENCY` | `str` | 0 (0.00%) | `Varanasi`, `Sitting Rajya Sabha` | Geography | Constituency name or RS category. |
| `IDA_NAME` | `str` | 0 (0.00%) | `DM Varanasi`, `DC Bengaluru Urban`| Implementing Authority | Implementing District Authority responsible for sanctioning. |
| `MP_NAME` | `str` | 0 (0.00%) | `Shri Narendra Modi` | Descriptive Entity | Legal name and term of sponsoring MP. |
| `TENURE` | `str` | 0 (0.00%) | `18th Lok Sabha`, `Sitting MP` | Term Label | Parliamentary term classification. |
| `TENURE_START_DATE` | `str` (Timestamp) | 0 (0.00%) | `Jun 4, 2024 12:00:00 AM` | Temporal Bound | Official commencement timestamp of MP's tenure. |
| `TENURE_END_DATE` | `str` (Timestamp) | 0 (0.00%) | `Jun 3, 2029 11:59:59 PM` | Temporal Bound | Scheduled expiration timestamp of MP's tenure. |
| `FILE_STATUS` | `object` (`bool`) | LS: 83,153 (76.00%), RS: 17,211 (67.06%)| `True`, `NaN` | Compliance Flag | Indicates whether an attachment record is associated on portal. |
| `ATTACH_ID` | `float64` | LS: 83,153 (76.00%), RS: 17,211 (67.06%)| `1864291.0`, `2183894.0` | Secondary Foreign Key | Internal group pointer to retrieve attachments via `/getAttachIdsbyFlag`. |

### 3.2 Works Sanctioned (`FLAG = 2`)
- **Source Datasets:** `mplads_lok_sabha_sanctioned.csv` (81,466 rows), `mplads_rajya_sabha_sanctioned.csv` (20,045 rows)

| Column Name | Inferred Dtype | Null Count (Rate %) | Example Values | Semantic Role | Analytical Definition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SANCTION_DATE` | `str` (Date) | 0 (0.00%) | `22-Aug-2024`, `10-Mar-2025` | **Temporal Benchmark** | Date District Authority issued formal administrative sanction. |
| `SANCTION_AMOUNT` | `float64` | 0 (0.00%) | `495000.0`, `1200000.0` | **Financial Ceiling** | Maximum legally approved budget ceiling in Rupees (₹). |
| `FLAG` | `int64` | 0 (0.00%) | `2` | Milestone Flag | Fixed at `2`, designating the administrative sanction milestone. |
| *Inherited Fields* | — | 0 (0.00%) | — | Multi-Dimensional | `Sno`, `LETTER_NO`, `ACTIVITY_NAME`, `WORK_CATEGORY`, `WORK_DESCRIPTION`, `STATE_NAME`, `CONSTITUENCY_ID`, `CONSTITUENCY`, `IDA_NAME`, `MP_NAME`, `TENURE`, `TENURE_START_DATE`, `TENURE_END_DATE`, `FILE_STATUS`, `ATTACH_ID` retain identical semantics. |

### 3.3 Works Completed (`FLAG = 3`)
- **Source Datasets:** `mplads_lok_sabha_completed.csv` (35,557 rows), `mplads_rajya_sabha_completed.csv` (10,147 rows)

| Column Name | Inferred Dtype | Null Count (Rate %) | Example Values | Semantic Role | Analytical Definition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `WORK_ID` | `int64` | 0 (0.00%) | `148495`, `192031` | Registry Counter | **Completion register counter unique ONLY to completed dataset.** |
| `ACTUAL_AMOUNT` | `float64` | 0 (0.00%) | `487500.0`, `0.0` | **Financial Actual** | Final cost recorded at project completion in Rupees (₹). |
| `ACTUAL_END_DATE` | `str` (Date) | 0 (0.00%) | `09-Dec-2025`, `07-May-2025` | **Temporal Benchmark** | Date of physical completion recorded on portal. Format: `DD-Mon-YYYY`. |
| `AVERAGE_RATING` | `float64` | 0 (0.00%) | `0.0`, `5.0` | Citizen Metric | Public citizen feedback rating (0.0 to 5.0). 99.9% are unrated (`0.0`). |
| `FLAG` | `int64` | 0 (0.00%) | `3` | Milestone Flag | Fixed at `3`, designating formal asset completion and handover. |
| `ATTACH_ID` | `float64` | LS: 9,302 (26.16%), RS: 3,458 (34.09%) | `1836498.0`, `1355528.0` | Secondary Foreign Key | Attachment group pointer associated with completion record. |
| `FILE_STATUS` | `object` (`bool`) | LS: 9,302 (26.16%), RS: 3,458 (34.09%) | `True`, `NaN` | Compliance Flag | Indicates whether an attachment record is associated on portal. |
| *Inherited Fields* | — | 0 (0.00%) | — | Multi-Dimensional | `Sno`, `LETTER_NO`, `ACTIVITY_NAME`, `WORK_CATEGORY`, `WORK_DESCRIPTION`, `STATE_NAME`, `CONSTITUENCY_ID`, `CONSTITUENCY`, `IDA_NAME`, `MP_NAME` retain identical semantics. |

### 3.4 Work Expenditures (Payment Vouchers)
- **Source Datasets:** `mplads_lok_sabha_expenditures.csv` (89,715 rows), `mplads_rajya_sabha_expenditures.csv` (22,220 rows)

| Column Name | Inferred Dtype | Null Count (Rate %) | Example Values | Semantic Role | Analytical Definition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `WORK_ID` | `str` | 0 (0.00%) | `WS/MP18398/2026-2027/243454` | Composite Reference | **Formatted activity string embedding DTL_ID (NOT the completed register counter).** |
| `WORK_RECOMMENDATION_DTL_ID`| `int64` | 0 (0.00%) | `18398`, `192454` | **Relational Foreign Key** | Primary join key linking payment voucher directly to parent Work. |
| `EXPENDITURE_DATE` | `str` (Date) | 0 (0.00%) | `14-Jan-2025`, `28-Feb-2026` | **Temporal Transaction** | Date disbursement voucher was approved in district treasury. |
| `FUND_DISBURSED_AMT` | `float64` | 0 (0.00%) | `150000.0`, `0.01` | **Financial Debit** | Amount disbursed in this payment tranche in Rupees (₹). |
| `PAYMENT_STATUS` | `str` | 0 (0.00%) | `Payment Successful` | Treasury Status | Transaction clearance state. 100% are successful. |
| `VENDOR_ID` | `int64` | 0 (0.00%) | `84920`, `124905` | Commercial Entity ID | System-wide unique identifier for payee commercial entity. |
| `VENDOR_NAME` | `str` | 0 (0.00%) | `M/S Sharma Constructions` | Commercial Entity Name | Registered business or individual contractor receiving funds. |
| `IA_NAME` | `str` | 0 (0.00%) | `Executive Engineer PWD Div 1`| Executing Agency | Specific technical/engineering agency supervising execution. |
| *Inherited Fields* | — | 0 (0.00%) | — | Multi-Dimensional | `STATE_NAME`, `CONSTITUENCY_ID`, `CONSTITUENCY`, `IDA_NAME`, `MP_NAME`, `WORK_STAGE` retain identical semantics. |

### 3.5 MP Allocations & Entitlements
- **Source Datasets:** `mplads_lok_sabha_allocations.csv` (543 rows), `mplads_rajya_sabha_allocations.csv` (232 rows)

| Column Name | Inferred Dtype | Null Count (Rate %) | Example Values | Semantic Role | Analytical Definition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `MP_NAME` | `str` | 0 (0.00%) | `Shri Rahul Gandhi` | Descriptive Entity | Legal name of MP owning entitlement ledger. |
| `TENURE` | `str` | 0 (0.00%) | `18th Lok Sabha`, `Sitting MP` | Term Label | Parliamentary term governing allocation ledger. |
| `ALLOCATED_AMT` | `float64` | 0 (0.00%) | `50000000.0`, `25000000.0` | **Financial Limit** | Total statutory entitlement funds allocated in Rupees (₹). |

### 3.6 Natural Calamity Relief Consents
- **Source Datasets:** `mplads_lok_sabha_calamity.csv` (14 rows), `mplads_rajya_sabha_calamity.csv` (18 rows)

| Column Name | Inferred Dtype | Null Count (Rate %) | Example Values | Semantic Role | Analytical Definition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CALAMITY_NAME` | `str` | 0 (0.00%) | `Kerala Wayanad Landslide 2024`| Disaster Event | Formal gazette title of declared natural calamity. |
| `CONSENTED_AMOUNT` | `float64` | 0 (0.00%) | `2500000.0`, `10000000.0` | **Financial Surrender** | Amount surrendered by MP under Para 5.1 of scheme rules. |
| `TYPE` | `str` | 0 (0.00%) | `Severe`, `State Level` | Disaster Category | Severity level governing surrender ceiling. |

---

## 4. Rajya Sabha Identifier Collision Resolution

A critical finding of the Phase 0 audit is that sequence identifier collisions exist within the Rajya Sabha recommendation records:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        RAJYA SABHA IDENTIFIER COLLISION PROFILE                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Affected Dataset:             mplads_rajya_sabha_recommended.csv                       │
│ Duplicate Sequence IDs:       Exactly 46 distinct WORK_RECOMMENDATION_DTL_ID values     │
│ Affected Rows:                Exactly 92 rows (pairs of 2 records sharing one ID)       │
│ Within-House Uniqueness:      100% of duplicate pairs represent DIFFERENT public works  │
│ Downstream Sanctions:         46 / 46 (100.0%) link exclusively to modern WS/MP record │
│ Unsanctioned Records:         46 / 46 (100.0%) of legacy NA- records were never funded │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Empirical Proof of Distinct Works & Root Cause
Deep inspection of all 46 duplicate pairs revealed:
1. **Completely Distinct Public Works:** In 100.0% of cases, the paired rows represent entirely separate projects initiated by different MPs in different states (e.g., a library in Maharashtra vs a road in Odisha).
2. **Root Cause (Legacy Portal Migration Sequence Overlap):** In every duplicate pair, exactly one row features an `ACTIVITY_NAME` starting with legacy prefix `"NA-"`, while the other features a standard e-SAKSHI prefix (`"WS/MP..."`). During initial data migration into e-SAKSHI, legacy pre-migration records were assigned sequence numbers overlapping with newly initiated digital recommendations.
3. **Downstream Sanction Linkage:** Across all 46 collision IDs, **zero duplicates exist in sanctions**. Exactly one row per pair reached administrative sanction—and in **100.0% of cases (46/46)**, the sanctioned work matches the modern `"WS/MP..."` record. Zero `"NA-"` records were ever sanctioned.
4. **Resolution via Dispatch Reference:** Including the MP's dispatch letter reference `LETTER_NO` completely eliminates all 46 duplicates:
   $$\mathbf{K}_{\text{work}} = (\text{HOUSE\_OF\_PARLIAMENT},\; \text{WORK\_RECOMMENDATION\_DTL\_ID},\; \text{LETTER\_NO})$$

---

## 5. Empirical Lifecycle Funnel & Stage Coverage

The 395,035 lifecycle records reconstruct the progressive funnel of public works from proposal to handover:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               EMPIRICAL LIFECYCLE FUNNEL                               │
├──────────────────────────────────────┬─────────────────────────────────────────────────┤
│ 1. Works Recommended (FLAG: 1)       │ 135,078 works (100.0% of proposed corpus)       │
│                                      │  └─ 109,412 Lok Sabha + 25,666 Rajya Sabha      │
├──────────────────────────────────────┼─────────────────────────────────────────────────┤
│ 2. Works Sanctioned (FLAG: 2)        │ 101,511 works (75.15% sanction conversion rate) │
│                                      │  ├─ 100,896 matched to recommendations          │
│                                      │  ├─ 615 orphan sanctions (unmatched to recs)    │
│                                      │  └─ 33,567 pending recommendation proposals     │
├──────────────────────────────────────┼─────────────────────────────────────────────────┤
│ 3. Works with Payments (Vouchers)    │ 73,448 sanctioned works (72.35% disbursement)   │
│                                      │  ├─ 111,935 payment vouchers (1..N cardinality) │
│                                      │  └─ 28,063 unspent sanctioned works in snapshot │
├──────────────────────────────────────┼─────────────────────────────────────────────────┤
│ 4. Completed Assets (FLAG: 3)        │ 45,704 completed assets (45.02% completion rate)│
│                                      │  ├─ 100.0% matched to Sanctions (0 orphans)     │
│                                      │  └─ 55,807 without observed completion record   │
├──────────────────────────────────────┼─────────────────────────────────────────────────┤
│ 5. Fully Linked End-to-End Works     │ 45,497 works (Rec ──► Sanc ──► Exp ──► Compl)   │
│                                      │  (45,605 completed works have payments)         │
└──────────────────────────────────────┴─────────────────────────────────────────────────┘
```

---

## 6. Data Quality Findings & Structural Invariants

Rigorous automated auditing across all 395,871 CSV rows established the following baseline quality findings:

### 6.1 Duplicate & Null Integrity
- **Exact Duplicate Rows:** **0 rows** across all 15 raw CSV files.
- **Core Identifiers:** **0% nulls** across all datasets for `WORK_RECOMMENDATION_DTL_ID`, `WORK_ID`, `MP_NAME`, `STATE_NAME`, `IDA_NAME`, and `VENDOR_ID`.
- **Temporal Fields:**
  - `RECOMMENDATION_DATE`: 0 nulls (135,078 / 135,078 valid).
  - `SANCTION_DATE` in Sanctions: 0 nulls (101,511 / 101,511 valid).
  - `SANCTION_DATE` in Recommendations: 34,182 nulls (corresponds to works pending sanction).
  - `ACTUAL_END_DATE` in Completions: 0 nulls (45,704 / 45,704 valid).
  - `EXPENDITURE_DATE` in Expenditures: 0 nulls (111,935 / 111,935 valid).
- **Textual Descriptions:** `WORK_DESCRIPTION` is 99.9% complete (114 nulls in LS Rec; 97 in LS Sanc; 79 in LS Compl; 7 in RS Compl).

### 6.2 Temporal Sequencing Integrity (0 Inverted Dates)
- An exploratory audit initially reported 177 instances of `SANCTION_DATE < RECOMMENDATION_DATE`.
- Exhaustive verification proved this was an artifact of unpartitioned cross-house joining. Lok Sabha and Rajya Sabha sequence numbers overlapped, causing a 2025 Lok Sabha proposal to cross-match with a 2023 Rajya Sabha sanction.
- Partitioned by chamber using $\mathbf{K}_{\text{work}}$:
  - Within Lok Sabha: `SANCTION_DATE < RECOMMENDATION_DATE` = **0**
  - Within Rajya Sabha: `SANCTION_DATE < RECOMMENDATION_DATE` = **0**
  - Across Completed: `ACTUAL_END_DATE < SANCTION_DATE` = **0**
- **Conclusion:** There are **zero temporal sequence contradictions** in the official e-SAKSHI data.

### 6.3 Documented Empirical Edge Cases
1. **Orphan Sanctions (615 records):** 615 sanctioned works (381 LS, 234 RS) have no recommendation record (`FLAG: 1`). Of these, 207 reached completion and 416 received payment. Handled by flagging `FLAG_ORPHAN_SANCTION = TRUE`.
2. **Zero-Cost Completions (97 records):** 97 completed works (77 LS, 20 RS) exhibit `ACTUAL_AMOUNT == 0.00`. Handled by flagging `FLAG_ZERO_COST_COMPLETION = TRUE`; variance evaluates to $-1.0$ ($-100\%$).
3. **Penny-Drop Banking Voucher (1 record):** Exactly 1 expenditure voucher has `FUND_DISBURSED_AMT == ₹0.01` (in Rajya Sabha), representing an automated bank account pre-validation check. Handled by flagging `FLAG_PENNY_DROP_PROBABLE = TRUE`.
4. **Cumulative Cost Overrun (1 record):** Across 45,704 completed works, exactly 1 work exhibited cumulative disbursements exceeding the sanction ceiling (by ₹5,000). The e-SAKSHI portal enforces hard financial limits at sanction.
5. **Completed Works with Zero Payments (99 records):** Exactly 99 completed works have no disbursement records in the expenditure dataset. Retained as valid completions with `HAS_EXPENDITURE = FALSE`.

---

# Part II: Canonical Domain Model & Relational Architecture

## 7. The Canonical Work Entity Definition

A foundational architectural requirement is establishing what constitutes a **Work**. In naive implementations, developers confuse milestone transaction records (recommendations, sanctions, or vouchers) with the project itself.

### 7.1 Core Work Entity vs. Milestone Child Records
> **The Canonical Work entity models the core identity, administrative context, and legal sponsorship of a public asset (Chamber, Sequence ID, Letter No, MP, State, Constituency, IDA, Category, Description). Lifecycle milestone observations (Recommendation, Sanction, Completion, Expenditures, Attachments) remain separate child entities linked via relational keys.**

| Analytical Field | Canonical Attribute | Source Field | Source Datasets | Data Type | Nullability | Provenance | Semantic Role & Operational Definition |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Identity** | `HOUSE_OF_PARLIAMENT` | `HOUSE_OF_PARLIAMENT` | All Work Datasets | `VARCHAR(16)` | **Required** | Source-Observed | Parliamentary chamber partition (`LOK_SABHA`, `RAJYA_SABHA`). |
| | `WORK_RECOMMENDATION_DTL_ID` | `WORK_RECOMMENDATION_DTL_ID` | All Work Datasets | `INT` | **Required** | Source-Observed | Natural backend sequence identifier. |
| | `LETTER_NO` | `LETTER_NO` | All Work Datasets | `VARCHAR(128)` | **Required** | Source-Observed | MP office dispatch reference. Disambiguates RS collisions. |
| | `ACTIVITY_NAME` | `ACTIVITY_NAME` | Rec, Sanc, Compl, Exp | `VARCHAR(512)` | **Required** | Source-Observed | Structured catalog activity code (e.g. `WS/MP18398/...`). |
| **2. Sponsoring MP**| `MP_NAME` | `MP_NAME` | All Datasets | `VARCHAR(128)` | **Required** | Source-Observed | Legal name and term of sponsoring MP (descriptive text). |
| **3. House & Term** | `TENURE` | `TENURE` | All Datasets | `VARCHAR(64)` | **Required** | Source-Observed | Term label (e.g. `18th Lok Sabha`, `Sitting MP`). |
| | `TENURE_START_DATE` | `TENURE_START_DATE` | Work & MP Datasets | `TIMESTAMP` | **Required** | Source-Observed | Official commencement timestamp of MP's tenure. |
| | `TENURE_END_DATE` | `TENURE_END_DATE` | Work & MP Datasets | `TIMESTAMP` | **Required** | Source-Observed | Scheduled expiration timestamp of MP's tenure. |
| **4. Geography** | `STATE_NAME` | `STATE_NAME` | All Datasets | `VARCHAR(64)` | **Required** | Source-Observed | State or Union Territory governing project location. |
| | `CONSTITUENCY_ID` | `CONSTITUENCY_ID` | Rec, Sanc, Compl, Alloc | `INT` | **Required** | Source-Observed | Constituency code (1–543 for LS; 545/546 for RS). |
| | `CONSTITUENCY` | `CONSTITUENCY` | Rec, Sanc, Compl, Alloc | `VARCHAR(128)` | **Required** | Source-Observed | Parliamentary Constituency name or RS category. |
| | `IDA_NAME` | `IDA_NAME` | Rec, Sanc, Compl, Exp | `VARCHAR(128)` | **Required** | Source-Observed | Implementing District Authority (DM, Collector, or DC). |
| **5. Sector** | `WORK_CATEGORY` | `WORK_CATEGORY` | Rec, Sanc, Compl | `VARCHAR(64)` | **Required** | Source-Observed | Sector category (`Normal/Others`, `Repair and Renovation`). |
| **6. Description** | `WORK_DESCRIPTION` | `WORK_DESCRIPTION` | Rec, Sanc, Compl | `TEXT` | Optional (0.1% null)| Source-Observed | Free-text technical project scope and site specs. |
| **7. Workflow** | `WORK_STAGE` | `WORK_STAGE` | Rec, Sanc | `VARCHAR(64)` | Optional (0.5% null)| Source-Observed | Observed workflow status label from portal. |

---

## 8. Hierarchical Work Identity Architecture

To ensure conceptual integrity across all lifecycle stages while preserving raw source data faithfully, the analytical engine formalizes a strict 4-tier identity hierarchy:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               WORK IDENTITY HIERARCHY                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Source Work Identity:        (HOUSE_OF_PARLIAMENT, WORK_RECOMMENDATION_DTL_ID)     │
│ 2. Recommendation Disambig:     LETTER_NO (Applied where 46 legacy collisions exist)   │
│ 3. Canonical Analytical Key:    (HOUSE_OF_PARLIAMENT, DTL_ID, LETTER_NO)               │
│ 4. Downstream Child Linkage:    (HOUSE, DTL_ID) [Where downstream uniqueness is proven]│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Source Work Identity:**
   $$\text{Source Identity} = (\text{HOUSE\_OF\_PARLIAMENT},\; \text{WORK\_RECOMMENDATION\_DTL\_ID})$$
   Within normal e-SAKSHI operation and single-house partitions, this natural key represents the native system identifier generated by the backend.
2. **Recommendation Disambiguation:**
   $$\text{Disambiguator} = \text{LETTER\_NO (Administrative Dispatch Reference)}$$
   In `mplads_rajya_sabha_recommended.csv`, exactly 46 sequence numbers appear twice (spanning 92 rows) due to legacy migration collisions between un-prefixed (`NA-`) and modern (`WS/MP...`) records. Because `LETTER_NO` is unique to each MP's dispatch, it reliably disambiguates all 46 collision pairs without altering raw source data.
3. **Canonical Analytical Work Key:**
   $$\mathbf{K}_{\text{work}} = (\text{HOUSE\_OF\_PARLIAMENT},\; \text{WORK\_RECOMMENDATION\_DTL\_ID},\; \text{LETTER\_NO})$$
   The authoritative primary key for the canonical Work entity. It guarantees 100.0% uniqueness across the full 135,078 recommendation corpus, ensuring no two distinct proposals are collapsed.
4. **Downstream Child Linkage:**
   $$\text{Downstream Join Key} = (\text{HOUSE\_OF\_PARLIAMENT},\; \text{WORK\_RECOMMENDATION\_DTL\_ID})$$
   Child entities (`Sanctions`, `Completed`, `Expenditures`) are linked using the 2-part tuple **strictly where empirical uniqueness of the downstream stage has been established**. Because zero collisions exist downstream (exactly 0 duplicate IDs exist in `Sanctions`, `Completed`, or within-voucher groups), this 2-part key safely resolves child records to their parent Work without requiring synthetic key injection into raw child tables.

### 8.1 Disqualification of `WORK_ID` as a Universal Key
Phase 0 empirically demonstrated that `WORK_ID` must never be used as a cross-stage primary key:
- **Datatype Conflict:** `int64` sequence in `Completed` (e.g. `148495`) vs formatted `str` in `Expenditures` (e.g. `WS/MP18275/.../243454`).
- **Semantic Divergence:** `WORK_ID` in `Completed` is an asset register counter; in `Expenditures` it is an activity code embedding `DTL_ID`.
- **Zero Match Rate:** Direct cross-joining of `Completed` to `Expenditures` on `WORK_ID` yields **0.00% matches (0 / 45,704)**.
- **Absence in Upstream Stages:** Neither `Recommended` nor `Sanctioned` contains a `WORK_ID` column.

### 8.2 Sponsoring MP Representation
MP identity is represented using the descriptive tuple `(HOUSE_OF_PARLIAMENT, MP_NAME, TENURE)`. MoSPI records MP names as free text without unique civil service or parliamentarian IDs. The engine treats names as descriptive labels rather than guaranteed primary keys, avoiding unsafe string normalization or pseudo-ID generation.

---

## 9. Relational Entity Model & Join Key Specifications

The analytical foundation defines **11 distinct entities** organized to preserve native cardinalities:

```text
                               ┌───────────────────────────┐
                               │        MP / TENURE        │
                               │  (Descriptive: MP_NAME,   │
                               │   HOUSE, TENURE)          │
                               └─────────────┬─────────────┘
                                             │
                     ┌───────────────────────┼───────────────────────┐
                     │ 1:1                   │ 1:M                   │ 1:M
                     ▼                       ▼                       ▼
          ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
          │     ALLOCATION      │ │   CALAMITY CONSENT  │ │   CANONICAL WORK    │
          │   (MP Spending      │ │  (Disaster Relief   │ │ (Core Identity &    │
          │    Entitlement)     │ │   Surrenders)       │ │  Admin Context)     │
          └─────────────────────┘ └─────────────────────┘ └──────────┬──────────┘
                                                                     │
                                     ┌───────────────────────────────┴───────────────────────────────┐
                                     │ 1:1 (Optional)                                                │ 1:1 (Optional)
                                     ▼                                                               ▼
                          ┌─────────────────────┐                                         ┌─────────────────────┐
                          │   RECOMMENDATION    │                                         │      SANCTION       │
                          │   (Proposal Event:  │                                         │ (Approval Event:    │
                          │    Date, Proposed ₹)│                                         │  Date, Sanction ₹)  │
                          └─────────────────────┘                                         └──────────┬──────────┘
                                                                                                     │
                                     ┌───────────────────────────────────────────────────────────────┴───────────────────────────────┐
                                     │ 1:1 (Optional)                                                                                │ 1:M (Optional)
                                     ▼                                                                                               ▼
                          ┌─────────────────────┐                                                                         ┌─────────────────────┐
                          │     COMPLETION      │                                                                         │     EXPENDITURE     │
                          │  (Handover Event:   │                                                                         │ (Payment Event:     │
                          │   Actual Date, ₹)   │                                                                         │  Voucher Date, ₹)   │
                          └──────────┬──────────┘                                                                         └──────────┬──────────┘
                                     │                                                                                               │
                                     │ 1:M (Optional)                                                                ┌───────────────┴───────────────┐
                                     ▼                                                                               │ M:1                           │ M:1
                          ┌─────────────────────┐                                                                    ▼                               ▼
                          │     ATTACHMENT      │                                                         ┌─────────────────────┐         ┌─────────────────────┐
                          │ (Document Pointer:  │                                                         │       VENDOR        │         │ IMPLEMENTING AGENCY │
                          │  Inspection Photos) │                                                         │    (VENDOR_ID)      │         │      (IA_NAME)      │
                          └─────────────────────┘                                                         └─────────────────────┘         └─────────────────────┘
```

### 9.1 Relational Join Key Specifications

| Target Join Relationship | Left Entity | Right Entity | Operational Join Key | Cardinality | Empirical Match % (Left $\rightarrow$ Right) | Join Integrity Finding |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Recommendation $\rightarrow$ Sanction** | Recommended | Sanctioned | `(HOUSE, DTL_ID, LETTER_NO)` | $1 \rightarrow 1$ | 74.70% $\rightarrow$ **99.39%** | 100,896 matched works; 33,567 pending; 615 orphan sanctions. 0 cross-house collisions. |
| **Sanction $\rightarrow$ Completion** | Sanctioned | Completed | `(HOUSE, DTL_ID, LETTER_NO)` | $1 \rightarrow 1$ | 45.02% $\rightarrow$ **100.00%** | 45,704 completed assets; 55,807 sanctioned works without an observed completion record. Zero orphan completions. |
| **Sanction $\rightarrow$ Expenditure** | Sanctioned | Expenditures | `(HOUSE, DTL_ID)` | $1 \rightarrow \text{Many}$ | 72.35% $\rightarrow$ **100.00%** | 73,448 sanctioned works have disbursements; 28,063 have no observed expenditure in snapshot. Zero orphan payments. |
| **Completion $\rightarrow$ Expenditure** | Completed | Expenditures | `(HOUSE, DTL_ID)` | $1 \rightarrow \text{Many}$ | **99.78%** $\rightarrow$ 61.34% | 45,605 completed assets have expenditure records; 99 completed lack payment records. |
| **Completion $\rightarrow$ Expenditure (via WORK_ID)**| Completed | Expenditures | `WORK_ID` | N/A | **0.00%** $\rightarrow$ **0.00%** | **Incompatible datatypes** (integer sequence vs formatted string). Must NOT be used. |
| **Expenditure $\rightarrow$ Vendor** | Expenditures | Commercial Vendors | `VENDOR_ID` | $\text{Many} \rightarrow 1$ | **100.00%** $\rightarrow$ **100.00%** | 30,839 unique vendors mapped across 111,935 transactions. 0% nulls. |
| **Expenditure $\rightarrow$ IA** | Expenditures | Implementing Agencies | `IA_NAME` | $\text{Many} \rightarrow 1$ | **100.00%** $\rightarrow$ **100.00%** | 7,378 distinct executing agencies mapped. Observed exclusively on works with payments. |
| **MP $\rightarrow$ Allocations** | Recommendations | Allocations | `(HOUSE, MP_NAME, TENURE)` | $\text{Many} \rightarrow 1$ | **100.00%** $\rightarrow$ 95.10% | 737 MPs matched (538 LS, 199 RS). 38 MPs in allocation ledger have 0 recommendations (5 LS, 33 RS). |

---

## 10. Lifecycle Model: Execution with Parallel Event Streams

The MPLADS project lifecycle is not a purely linear conveyor belt where expenditure must precede completion. Once a project receives administrative sanction, it enters the **Execution** phase. During execution, two asynchronous streams occur concurrently:
1. **Expenditure Events ($0..N$):** A stream of zero, one, or multiple payment vouchers released to vendors.
2. **Completion Milestone ($0..1$):** A formal administrative handover event certifying physical completion.

```text
┌─────────────────────────────────────────┐
│            1. RECOMMENDATION            │ ──► Proposed by MP (135,078 works)
└────────────────────┬────────────────────┘
                     │ (75.15% Sanction Rate; 100,896 matched)
                     ▼
┌─────────────────────────────────────────┐
│               2. SANCTION               │ ──► Approved by DA (101,511 works; incl. 615 orphan sanctions)
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          3. EXECUTION PHASE                             │
│                                                                         │
│   ┌────────────────────────────────┐   ┌────────────────────────────┐   │
│   │    EXPENDITURE STREAM (0..N)   │   │   COMPLETION EVENT (0..1)  │   │
│   │  • Voucher 1 (Advance/Tranche) │   │  • Final Certificate Date  │   │
│   │  • Voucher 2 (Interim Payment) │   │  • Recorded Completion Cost│   │
│   │  • Voucher N (Final Payment)   │   │  • Citizen Rating (0.0-5.0)│   │
│   └────────────────────────────────┘   └────────────────────────────┘   │
│         (73,448 works paid;                  (45,704 works completed;   │
│          111,935 total vouchers)              45,605 with payments)     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.1 Stage Categorization Mapping
The engine maps project progress into four mutually exclusive operational states:

| Lifecycle Stage Code | State Definition | Operational Criteria | Observed Count |
| :--- | :--- | :--- | :--- |
| `RECOMMENDED_UNSANCTIONED` | Proposed; awaiting sanction | `FLAG == 1` and no matching sanction row. | **33,567 works** |
| `SANCTIONED_UNPAID` | Sanctioned; zero disbursements | Sanction observed, 0 payment vouchers, not completed. | **27,964 works** |
| `IN_PROGRESS_DISBURSING` | Sanctioned; active payments | Sanction observed, $\ge 1$ payment voucher, not completed. | **27,843 works** |
| `COMPLETED` | Physically certified complete | `FLAG == 3` (completion record observed). | **45,704 works** |

---

## 11. Financial Semantics & Additive Safety Invariants

### 11.1 Field Definitions & Interpretations
- `RECOMMENDED_AMOUNT`: Estimated project budget proposed by MP in Indian Rupees (₹). Non-binding advisory figure.
- `SANCTION_AMOUNT`: Legally approved administrative liability limit authorized by the District Authority. Hard statutory ceiling.
- `FUND_DISBURSED_AMT`: Actual treasury disbursement recorded on an individual payment voucher tranche.
- `ACTUAL_AMOUNT`: Final reported completion cost recorded at project handover.

### 11.2 Additive Safety Invariants (Prohibition of Cross-Voucher Summing)
1. **Never Sum Sanction Amounts Across Vouchers:**
   Joining Sanctions to Expenditures replicates `SANCTION_AMOUNT` across all vouchers. If a project has 5 vouchers, summing `SANCTION_AMOUNT` multiplies the approved liability by 5. Summation is mathematically valid **only** over deduplicated Work entities.
2. **Never Sum Actual Amounts Across Vouchers:**
   Joining Completion records to Expenditures replicates `ACTUAL_AMOUNT` across every voucher. Summing `ACTUAL_AMOUNT` across joined rows produces duplicate copies of the completion cost.
3. **Additive Invariant for Expenditures:**
   $$\text{TOTAL\_DISBURSED\_AMT} = \sum_{i=1}^{N} \text{FUND\_DISBURSED\_AMT}_i$$
   Summing is mathematically valid **only** across voucher records for a single work.
4. **Disbursement Null Invariant:**
   For works with zero expenditure rows, `TOTAL_DISBURSED_AMT` must evaluate to `NULL`, **not ₹0.00**. Assigning ₹0.00 conflates an unobserved financial stage with a recorded financial transaction of zero value.

---

## 12. Temporal Milestones & Interval Formulations

All dates in e-SAKSHI are formatted as `DD-Mon-YYYY` (e.g. `15-Jul-2024`). The engine normalizes timestamps to ISO-8601 (`YYYY-MM-DD`) and computes three standard duration intervals:

1. **Sanction Window:**
   $$\text{DAYS\_TO\_SANCTION} = \text{SANCTION\_DATE} - \text{RECOMMENDATION\_DATE}$$
   Evaluated against statutory 45-day decision window (Para 3.12, MPLADS 2023 Guidelines).
2. **Disbursement Initiation Window:**
   $$\text{DAYS\_TO\_FIRST\_PAYMENT} = \min(\text{EXPENDITURE\_DATE}) - \text{SANCTION\_DATE}$$
   Evaluated against official e-SAKSHI 3-month fund-inactivity monitoring threshold.
3. **Execution Completion Window:**
   $$\text{DAYS\_TO\_COMPLETION} = \text{ACTUAL\_END\_DATE} - \text{SANCTION\_DATE}$$
   Evaluated against official 1-year completion monitoring threshold (Standing Committee Report 35).

---

# Part III: Operational Rules, Metrics & Feasibility Scope

## 13. Missing-Data Taxonomy & Grounded Case Rules

To prevent erroneous analytical inferences, the engine enforces deterministic rules for unobserved or missing values:

### 13.1 Missing-Data Classification Taxonomy
1. **Structural Null:** Attribute absent by schema definition (e.g., `WORK_ID` does not exist in Recommendations or Sanctions).
2. **Absent Child Record:** Downstream milestone not yet observed (e.g., work has no completion or payment rows).
3. **Semantic Sentinel:** Value inapplicable to entity class (e.g., Nominated RS MPs have no geographic constituency).
4. **Not Yet Occurred:** Real-world event pending (e.g., recently sanctioned project under active construction).
5. **Unobserved in Snapshot:** Data exists offline or outside public API (e.g., base64 certificate PDFs, tender documents).
6. **Contradictory Record:** Cross-stage mismatch handled via explicit uncertainty markers.

### 13.2 Grounded Case Rules
- **Rule 1 (`No Sanction Record ≠ Rejected Work`):** 34,182 recommendations lack sanctions. e-SAKSHI exposes no public rejection log. The work may be under administrative review. Assign `LIFECYCLE_STAGE = 'RECOMMENDED_UNSANCTIONED'`. Do **not** classify as rejected.
- **Rule 2 (`No Expenditure Record ≠ Zero Expenditure`):** 28,063 sanctioned works have no expenditure rows. Physical construction may be underway with contractor billing pending. Assign `TOTAL_DISBURSED_AMT = NULL` and `HAS_EXPENDITURE = FALSE`. Do **not** classify as abandoned.
- **Rule 3 (`No IA_NAME ≠ Missing Implementing Agency in All Cases`):** `IA_NAME` is observed exclusively in Expenditures. For sanctioned works without payments, set `IA_NAME = NULL` and record `IA_OBSERVATION_STATUS = 'NOT_OBSERVED_PRE_PAYMENT'`. Missingness metadata must **not** be stored as an entity value (which would corrupt downstream agency grouping).
- **Rule 4 (`No Completion Record ≠ Stalled Work`):** 55,807 sanctioned works have no completion record (`FLAG: 3`). Projects take time to construct. Delay must be evaluated strictly relative to `SANCTION_DATE` and elapsed age at snapshot date, never purely on the absence of a completion record.
- **Rule 5 (`Nominated Rajya Sabha Geography`):** Nominated RS MPs have `CONSTITUENCY_ID = 546` and `CONSTITUENCY = 'Sitting Rajya Sabha'`. Map to `CONSTITUENCY_NAME = 'NOMINATED_STATEWIDE'`. Do **not** treat as missing geography.

---

## 14. Data-Quality Treatment Matrix for Analytical Pipelines

| Empirical Edge Case | Observed Scope in Phase 0 | Root Cause / Mechanism | Analytical Engine Treatment | Quality Flag & Uncertainty Marker |
| :--- | :--- | :--- | :--- | :--- |
| **Rajya Sabha Sequence Collisions** | 46 duplicate IDs across 92 rows in RS Rec | Legacy migration sequence collision between `NA-` and `WS/MP...` records. | Disambiguated by `LETTER_NO` in $\mathbf{K}_{\text{work}}$. | Key disambiguation resolves 100.0%. Both records preserved. |
| **Orphan Sanctions** | Exactly 615 sanctioned works lack recommendation row | Ingestion cutoff, disaster fast-track entry, or legacy migration gap. | Ingest into Work model with null recommendation attributes. | Set `FLAG_ORPHAN_SANCTION = TRUE`. Excluded from rec-to-sanc delay metrics. |
| **Zero-Cost Completions** | Exactly 97 completed works exhibit `ACTUAL_AMOUNT == 0.00` | Administrative cancellation record, convergence funding, or clerical zero-entry. | Ingest verbatim as observed source record. | Set `FLAG_ZERO_COST_COMPLETION = TRUE`. Evaluated in cost-variance ratios as `-1.0` (-100% variance vs sanction). |
| **Penny-Drop Banking Voucher** | Exactly 1 voucher has `FUND_DISBURSED_AMT == ₹0.01` | Automated bank account pre-validation check prior to bulk release. | Ingest verbatim as observed payment record. | Set `FLAG_PENNY_DROP_PROBABLE = TRUE`. Retained in voucher counts; excluded from vendor volume rankings. |
| **Missing Documentary Attachments** | 67.77% null in LS Sanctions; 26.16% null in LS Completed | Document upload backlog or unassociated portal attachment record. | Ingest `FILE_STATUS` and `ATTACH_ID` verbatim. | Set `FLAG_DOCUMENT_ATTACHED = FALSE`. Evaluated strictly as attachment-presence indicator, not proof of missing certificate. |
| **Completed Works with Zero Payments**| Exactly 99 completed works lack expenditure records | Unobserved administrative reason (not established from portal data). | Retained in Completed model with `HAS_EXPENDITURE = FALSE`. | Retained as valid completed works; excluded from payment-timing metrics. |

---

## 15. Separation of Source Observations vs. Derived Metrics

To maintain architectural transparency, the engine strictly separates raw source observations from derived computational metrics:

### 15.1 Source-Observed Fields (Raw Facts)
- `HOUSE_OF_PARLIAMENT`, `WORK_RECOMMENDATION_DTL_ID`, `LETTER_NO`, `ACTIVITY_NAME`, `WORK_CATEGORY`, `WORK_DESCRIPTION`, `STATE_NAME`, `CONSTITUENCY_ID`, `CONSTITUENCY`, `IDA_NAME`, `MP_NAME`, `TENURE`, `TENURE_START_DATE`, `TENURE_END_DATE`
- `RECOMMENDATION_DATE`, `RECOMMENDED_AMOUNT`
- `SANCTION_DATE`, `SANCTION_AMOUNT`, `FLAG` (2)
- `WORK_ID` (in Completed), `ACTUAL_END_DATE`, `ACTUAL_AMOUNT`, `AVERAGE_RATING`, `FLAG` (3)
- `EXPENDITURE_DATE`, `FUND_DISBURSED_AMT`, `PAYMENT_STATUS`, `VENDOR_ID`, `VENDOR_NAME`, `IA_NAME`
- `ALLOCATED_AMT`, `CONSENTED_AMOUNT`, `CALAMITY_NAME`, `TYPE` (Calamity), `ATTACH_ID`, `FILE_STATUS`

### 15.2 Derived Analytical Fields (Future Computational Metrics)
These derived fields are formally defined here for architectural alignment; they will be computed during Phase 1 (Core Detection) and Phase 2 (Pattern Intelligence):

| Derived Field Name | Entity Level | Analytical Purpose | Mathematical Formula / Logical Definition | Input Field(s) | Edge Case & Null Treatment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `WORK_KEY` | Work | Authoritative Work PK | `CONCAT(HOUSE, '_', DTL_ID, '_', LETTER_NO)` | `HOUSE`, `DTL_ID`, `LETTER_NO` | Inputs mandatory; never null. |
| `HAS_EXPENDITURE` | Work | Payment occurrence flag | `CASE WHEN COUNT(Vouchers) > 0 THEN TRUE ELSE FALSE END` | Vouchers table | Deterministic boolean (`TRUE` / `FALSE`). |
| `TOTAL_DISBURSED_AMT` | Work | Cumulative disbursements | $\sum \text{FUND\_DISBURSED\_AMT}$ across vouchers for work | `FUND_DISBURSED_AMT` | **Returns `NULL` if `HAS_EXPENDITURE = FALSE`.** |
| `VOUCHER_COUNT` | Work | Payment transaction count| $\text{COUNT}(\text{Voucher})$ across vouchers for work | `FUND_DISBURSED_AMT` | If 0 vouchers exist, returns `0`. |
| `VENDOR_COUNT` | Work | Number of distinct vendors| $\text{COUNT}(\text{DISTINCT } \text{VENDOR\_ID})$ for work | `VENDOR_ID` | If 0 vouchers exist, returns `0`. |
| `LIFECYCLE_STAGE` | Work | Operational progress state| Finite state mapping (Section 10.1) | `FLAG`, `SANCTION_DATE`, vouchers | Defaults to `'RECOMMENDED_UNSANCTIONED'`. |
| `FINANCIAL_UTILIZATION_RATIO`| Work | Sanction utilization rate| $\frac{\text{TOTAL\_DISBURSED\_AMT}}{\text{SANCTION\_AMOUNT}}$ | `TOTAL_DISBURSED_AMT`, `SANCTION_AMOUNT` | If `SANCTION_AMOUNT IS NULL`, `== 0`, or `TOTAL_DISBURSED_AMT IS NULL`, returns `NULL`. |
| `COST_VARIANCE_SANCTION_TO_REC`| Work | Sanction vs proposal drift| $\frac{\text{SANCTION\_AMOUNT} - \text{RECOMMENDED\_AMOUNT}}{\text{RECOMMENDED\_AMOUNT}}$ | `SANCTION_AMOUNT`, `RECOMMENDED_AMOUNT` | If either is null or `RECOMMENDED_AMOUNT == 0`, returns `NULL`. |
| `COST_VARIANCE_ACTUAL_TO_SANC`| Work | Completion vs sanction drift| $\frac{\text{ACTUAL\_AMOUNT} - \text{SANCTION\_AMOUNT}}{\text{SANCTION\_AMOUNT}}$ | `ACTUAL_AMOUNT`, `SANCTION_AMOUNT` | If `SANCTION_AMOUNT IS NULL`, `== 0`, or `ACTUAL_AMOUNT IS NULL`, returns `NULL`. When `ACTUAL_AMOUNT == 0`, evaluates to `-1.0` (-100% variance) with `FLAG_ZERO_COST_COMPLETION = TRUE`. |
| `DAYS_TO_SANCTION` | Work | Recommendation to sanction| $\text{SANCTION\_DATE} - \text{RECOMMENDATION\_DATE}$ | `SANCTION_DATE`, `RECOMMENDATION_DATE` | If either date is null, returns `NULL`. |
| `DAYS_TO_FIRST_PAYMENT` | Work | Sanction to first voucher | $\min(\text{EXPENDITURE\_DATE}) - \text{SANCTION\_DATE}$ | `SANCTION_DATE`, `EXPENDITURE_DATE` | If either date is null, returns `NULL`. |
| `DAYS_TO_COMPLETION` | Work | Sanction to completion | $\text{ACTUAL\_END_DATE} - \text{SANCTION\_DATE}$ | `ACTUAL_END_DATE`, `SANCTION_DATE` | If either date is null, returns `NULL`. |
| `DAYS_COMPLETION_TO_FINAL_PAYMENT`| Work | Completion to final voucher| $\max(\text{EXPENDITURE\_DATE}) - \text{ACTUAL\_END_DATE}$ | `ACTUAL_END_DATE`, `EXPENDITURE_DATE` | If either date is null, returns `NULL`. |
| `PAYMENT_SPAN_DAYS` | Work | Disbursement duration | $\max(\text{EXPENDITURE\_DATE}) - \min(\text{EXPENDITURE\_DATE})$ | `EXPENDITURE_DATE` | If < 2 vouchers exist, returns `0`. |
| `HAS_ATTACHMENT` | Work | Attachment indicator | `CASE WHEN ATTACH_ID IS NOT NULL OR FILE_STATUS = 'True' THEN TRUE ELSE FALSE END` | `ATTACH_ID`, `FILE_STATUS` | Evaluates deterministically to `FALSE`. |
| `VENDOR_MARKET_SHARE_IDA` | Vendor | Vendor volume dominance | $\frac{\sum \text{FUND\_DISBURSED\_AMT}_{\text{Vendor, IDA}}}{\sum \text{FUND\_DISBURSED\_AMT}_{\text{IDA}}}$ | `FUND_DISBURSED_AMT`, `VENDOR_ID`, `IDA_NAME` | Evaluated within Implementing District Authority (`IDA_NAME`) as available administrative proxy; returns `NULL` if IDA total is 0. |

---

## 16. Anomaly Detector Feasibility Taxonomy

The analytical anomaly detectors specified in [`Core.md`](Core.md) are classified into three feasibility tiers based strictly on observed data availability:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      DETECTOR FEASIBILITY TAXONOMY                     │
├───────────────────┬────────────────────────────────────────────────────┤
│ GREEN (Supported) │ Fully supported by complete, verified data fields. │
│ YELLOW (Limited)  │ Supported with material schema/granularity caveats.│
│ RED (Unsupported) │ Barred; required data absent from e-SAKSHI schema. │
└───────────────────┴────────────────────────────────────────────────────┘
```

### 16.1 GREEN — Directly Supported Detectors

| Detector ID | Detector Title | Target Phase | Supporting Observed Fields | Baseline / Regulatory Logic | Empirical Coverage & Feasibility Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D1** | **Statutory Sanction Delay Detector** | **Phase 1** (Compliance) | `RECOMMENDATION_DATE`, `SANCTION_DATE` | Evaluates delay against statutory 45-day decision window (Para 3.12, MPLADS 2023 Guidelines; Lok Sabha Question *44). | **100,896 matched works (99.39% of sanctions).** 0 inverted dates. |
| **D2** | **Completion Timeline & Stagnation Detector** | **Phase 1** (Execution) | `SANCTION_DATE`, `ACTUAL_END_DATE`, `WORK_STATUS` | Evaluates completion duration against official 1-year monitoring threshold (Standing Committee Report 35). | **45,704 completed works; 55,807 sanctioned works without an observed completion record (evaluated by sanction age).** |
| **D3** | **Fund Dormancy / Payment Inactivity Detector**| **Phase 1** (Compliance) | `SANCTION_DATE`, `EXPENDITURE_DATE`, `FUND_DISBURSED_AMT` | Evaluates payment inception against official eSAKSHI monitoring threshold: no payment within 3 months of sanction. | **16,694 dormant works (sanctioned $\ge 3$ months with no payment); 11,369 unspent works sanctioned $< 3$ months are not yet eligible.** (Total unspent: 28,063; paid: 73,448). |
| **D4** | **Vendor Concentration Profiler** | **Phase 2** (Relationships) | `VENDOR_ID`, `VENDOR_NAME`, `IDA_NAME`, `FUND_DISBURSED_AMT` | Computes statistical market concentration (HHI) and volume dominance within district authority. | **111,935 transactions; 30,839 vendor IDs (0% nulls).** Strictly measures market share. |
| **D5** | **Textual Recommendation Repetition Detector**| **Phase 2** (Similarity) | `WORK_DESCRIPTION`, `RECOMMENDED_AMOUNT`, `IDA_NAME` | Identifies high-frequency identical or near-identical proposals via TF-IDF / Levenshtein clustering. | **135,078 recommendations (99.9% complete descriptions).** Strictly measures text clustering. |
| **D6** | **Cost Estimation & Sanction Drift Profiler** | **Phase 1** (Financial) | `RECOMMENDED_AMOUNT`, `SANCTION_AMOUNT`, `ACTUAL_AMOUNT` | Evaluates variance ratios $\frac{\text{Sanction}}{\text{Recommend}}$ and $\frac{\text{Actual}}{\text{Sanction}}$ for statistical outlier behavior. | **Coverage disaggregated by scope:** 100,896 rec $\rightarrow$ sanction pairs; 45,704 sanction $\rightarrow$ actual pairs; 45,497 full 3-stage comparisons (207 completions lack recommendation data). |
| **D8** | **High-Frequency Recommendation Bursts** | **Phase 2** (Trends) | `RECOMMENDATION_DATE`, `LETTER_NO`, `MP_NAME` | Analyzes temporal submission patterns and proposal clustering at fiscal year-end or tenure transitions. | **135,078 recommendations (100% valid dates).** |
| **D9** | **Unsanctioned Recommendation Dormancy** | **Phase 1** (Compliance) | `RECOMMENDATION_DATE`, `WORK_STAGE` | Evaluates recommendations lacking administrative sanction beyond statutory review windows. | **33,567 pending recommendation records.** |

### 16.2 YELLOW — Materially Limited Detectors

| Detector ID | Detector Title | Observed Schema Constraint | Feasible Implementation Strategy |
| :--- | :--- | :--- | :--- |
| **D10** | **Intermediate Physical Progress Tracking** | e-SAKSHI provides administrative milestone labels (`Pending for Sanction`, `Sanction`, `Vendor Identification`) but does not publish quantitative physical completion percentages (e.g. 25%, 50%, 75%) or civil milestone inspection dates. | **Constrained by absence of quantitative physical progress:** Administrative stages are observed, but physical execution pacing cannot be measured quantitatively between sanction and completion. |
| **D11** | **Geospatial Site Clustering** | The public API does not expose GPS latitude/longitude coordinates (`/getGisData` returns 404). | **Limited to macro-administrative clustering:** District Magistrate jurisdiction (`IDA_NAME`) and Parliamentary Constituency. Pinpoint GIS site auditing is unsupported. |
| **D12** | **Documentary Attachment Association Profiler** | Document attachments exist as binary/base64 payloads via secondary API endpoints (`/getAttachmentById`), but document types are not distinguished in primary tabular metadata. | **Limited to attachment-presence indexing:** Prototype flags presence or absence of an associated attachment record (`ATTACH_ID` / `FILE_STATUS` populated). Does NOT establish certificate compliance without document payload inspection. |

### 16.3 RED — Infeasible & Excluded Capabilities

| Capability / Asserted Detector | Root Cause of Infeasibility | Strict Governance Mandate |
| :--- | :--- | :--- |
| **SC/ST Statutory Allocation Auditor (Formerly D7)** | `WORK_CATEGORY` reflects project types (`Normal/Others`, `Repair and Renovation`), NOT whether a work is located in an SC/ST area or qualifies toward statutory 15% SC / 7.5% ST earmarks. Demographic census mapping is absent. | **EXPLICITLY REMOVED / BARRED.** Do not invent an SC/ST compliance detector from insufficient data. |
| **Bid-Rigging / Tender Circumvention** | Procurement records (tenders, NITs, rival bidder rosters, L1-L2 margins) reside in GeM and state e-tendering portals, not e-SAKSHI. | **EXPLICITLY BARRED.** The prototype must never claim detection of bid-rigging or tender manipulation. |
| **Collusion / Cartelization Detection** | Detecting corporate collusion requires corporate registry data (MCA-21), shared directorships, common bank accounts, or IP logs. | **EXPLICITLY BARRED.** Must be framed strictly as "Vendor Market Concentration" or "Repeated Agency Pairing". |
| **Proof of Duplicate Physical Works** | Textual similarity between work descriptions (e.g., "Installation of Solar Street Light at Village X") often reflects standard catalog procurement. | **EXPLICITLY BARRED.** Must be framed strictly as "Textual Similarity Clustering Warranting Administrative Review". |
| **Fraud / Intentional Criminality** | Intent, corruption, and fraud cannot be established from administrative portal records without formal judicial/forensic investigation. | **EXPLICITLY BARRED.** The prototype will output purely neutral, objective statistical anomaly scores. |

---

## 17. External Reference Sources & Validation Integration

The prototype integrates external statutory documents and audit reports exclusively as **regulatory benchmarks and retrospective validation evidence**, never as primary transactional data tables:

1. **MPLADS Scheme Guidelines w.e.f. 1st April 2023:**
   - Authoritative source for regulatory compliance thresholds: Para 3.12 establishes the 45-day window for District Authorities to sanction or reject recommended works; Para 5.1 governs natural calamity surrender limits; Annexure-VIII lists permissible work categories.
2. **MoSPI Annual Reports (2023–24):**
   - Provides cumulative scheme figures since inception and post-2023 e-SAKSHI migration aggregates, used to validate the macro-level boundaries of the scraped corpus.
3. **Parliamentary Q&A Annexures (Lok Sabha Starred Question No. *44 of 22-Jul-2026):**
   - Establishes official e-SAKSHI administrative monitoring benchmarks: sanctions pending > 45 days, works incomplete > 1 year after sanction, and works with no payment within three months of sanction constitute official monitoring criteria under ministerial review.
4. **Comptroller and Auditor General (CAG) Performance Audit (Report No. 31 of 2010-11, Chapter 4):**
   - Serves as empirical validation for anomaly archetypes, confirming that administrative delays, unspent balances, repeat vendor contracts, and missing documentary attachments represent historical systemic vulnerabilities.

---

## 18. Known Limitations & Frozen Prototype Scope

The prototype development accounts for five structural limitations inherent to the raw administrative source data:

1. **Absence of Quantitative Physical Progress Measurements:** While e-SAKSHI records administrative workflow milestones (`WORK_STAGE` states), it does not publish quantitative physical completion percentages or milestone inspection dates. Execution duration is evaluated against terminal completion timestamps.
2. **Absence of GIS / GPS Spatial Coordinates:** The portal provides administrative geography (District, Constituency, Implementing Agency) but does not expose raw latitude/longitude points or polygon boundaries. Geospatial risk scoring remains aggregate at District / Constituency level.
3. **Pre-eSAKSHI Historical Truncation:** e-SAKSHI was introduced alongside revised MPLADS Guidelines w.e.f. 1st April 2023. Comprehensive digital tracking is available primarily for the 18th Lok Sabha and contemporary Rajya Sabha cycles.
4. **Decoupling from Public Procurement Platforms:** e-SAKSHI records financial releases and contract awards, but does not ingest tender bidding documents, bidder rosters, or rate contracts from state e-procurement portals or GeM.
5. **Asynchronous Administrative Data Entry:** District administrations enter sanction dates, completion certificates, and payment vouchers asynchronously. Delays observed reflect a combination of physical duration and administrative data-entry latency.

### 18.1 Frozen Prototype Scope Summary
- **Directly Supported:** Multi-stage lifecycle reconstruction (~101k sanctions, 45.6k fully linked); statutory and official timeline auditing (45-day sanction window, 1-year completion threshold, 3-month fund dormancy); vendor and agency market concentration (HHI); textual proposal repetition clustering; MP financial entitlement ceiling reconciliation.
- **Supported with Limitations:** Documentary attachment availability indexing (`ATTACH_ID` populated; deep OCR deferred); macro-administrative geographic concentration (IDA proxy); citizen feedback score tracking (<0.1% rated).
- **Unsupported (Explicitly Barred):** SC/ST quota auditing; fraud/corruption accusations; bid-rigging/tender manipulation; collusion/cartel proof; physical duplicate work determinations; on-site physical inspection reality.

---

## 19. Phase 0 Definition of Done & Sign-Off Verification

The data foundation and analytical model for the MPLADS Intelligence Engine are complete under the following checklist:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 0 DEFINITION OF DONE CHECKLIST                            │
├──────────────────────────────────────────────────────────────────┬─────────────────────┤
│ Criterion / Requirement                                          │ Status              │
├──────────────────────────────────────────────────────────────────┼─────────────────────┤
│ 1. Exhaustive file inventory across 15 CSV files (395,871 rows)  │ VERIFIED (Sec 2)    │
│ 2. Exact reconciliation against official e-SAKSHI counters       │ VERIFIED (Sec 2.1)  │
│ 3. Complete field-level data dictionary and nullability profiles │ VERIFIED (Sec 3)    │
│ 4. Rajya Sabha collision proof & LETTER_NO resolution established│ VERIFIED (Sec 4)    │
│ 5. Empirical lifecycle funnel and conversion rates documented    │ VERIFIED (Sec 5)    │
│ 6. Data quality findings (0 duplicate rows, 0 date inversions)   │ VERIFIED (Sec 6)    │
│ 7. Canonical Work definition separates core identity from events │ VERIFIED (Sec 7)    │
│ 8. Explicit 4-tier Work identity hierarchy established           │ VERIFIED (Sec 8)    │
│ 9. Disqualification of WORK_ID as universal key documented       │ VERIFIED (Sec 8.1)  │
│ 10. MP identity modeled via descriptive attributes (no pseudo-IDs)│ VERIFIED (Sec 8.2)  │
│ 11. 11-entity relational model & cross-stage join keys specified │ VERIFIED (Sec 9)    │
│ 12. Lifecycle models execution with parallel payment/completion  │ VERIFIED (Sec 10)   │
│ 13. Financial semantics and additive safety invariants formalized│ VERIFIED (Sec 11)   │
│ 14. Missing-data taxonomy & grounded rules (IA_NAME = NULL)      │ VERIFIED (Sec 13)   │
│ 15. Zero-cost completion variance evaluated cleanly as -1.0      │ VERIFIED (Sec 14-15)│
│ 16. Source-observed vs. derived fields separated (SHARE_IDA proxy)│ VERIFIED (Sec 15)   │
│ 17. Feasibility taxonomy bounds supported vs barred detectors    │ VERIFIED (Sec 16)   │
│ 18. Known data limitations & frozen scope boundaries formalized  │ VERIFIED (Sec 18)   │
│ 19. Zero implementation code executed (Specification Only)       │ VERIFIED            │
└──────────────────────────────────────────────────────────────────┴─────────────────────┘
```

**Phase 0 is complete. The consolidated data foundation and canonical analytical specification are locked for Phase 1 (Baselines & Core Detection) implementation.**
