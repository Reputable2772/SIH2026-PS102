# Phase 0 — Analytical Foundation & Canonical Model Specification
**MPLADS Intelligence Engine (SIH PS102)**  
**Authoritative Input Baseline:** `Phase 0 Data Audit (MPLADS/eSAKSHI — 2026-09-21 snapshot)`  
**Phase Mapping:** Phase 0 — Part 2 (Analytical Model & Canonical Domain Specification)  
**Status:** Canonical Analytical Specification (Aligned with 4-Phase Architecture)  
**Document Version:** 1.2.0 (Incorporating Architectural Review & Epistemic Controls)  

---

## 1. Executive Summary & Analytical Mandate

### 1.1 Scope and Objective
Under the 4-phase prototype implementation plan ([`docs/Core.md`](Core.md)), **Phase 0 (Data Foundation & Analytical Model)** integrates empirical auditing, canonical entity modeling, and relational staging. This document constitutes Part 2 of Phase 0, establishing the definitive analytical representation of the Member of Parliament Local Area Development Scheme (MPLADS) public data foundation. Building upon the empirical findings, reconciliation proofs, and scope boundaries frozen in the Phase 0 Data Audit ([`docs/PHASE_0_FINAL.md`](PHASE_0_FINAL.md)), this specification removes all semantic ambiguity regarding:
- What constitutes an analytical **Work** entity;
- How **Work Identity** is established and how legacy collisions are disambiguated;
- How **Lifecycle Stages** and parallel event streams progress;
- How **Expenditures, Vendors, and Implementing Agencies** relate to Works;
- How **Financial and Temporal Attributes** must be computed and aggregated;
- How **Missing, Unobserved, and Contradictory Data** must be treated;
- Which fields are **Source Observations** versus future **Derived Metrics**.

### 1.2 Data Inventory & Row Count Accounting
To avoid any terminological confusion across datasets, the exact composition of the scraped first-party dataset is defined as follows:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FIRST-PARTY DATA INVENTORY ACCOUNTING                     │
├─────────────────────────────────────────┬──────────────┬───────────────────────────────┤
│ Dataset Category                        │ Record Count │ Composition Details           │
├─────────────────────────────────────────┼──────────────┼───────────────────────────────┤
│ Work & MP Lifecycle Records (12 CSVs)   │ 395,035 rows │ Recommendations: 135,078      │
│                                         │              │ Sanctions:       101,511      │
│                                         │              │ Completions:      45,704      │
│                                         │              │ Expenditures:    111,935      │
│                                         │              │ MP Allocations:      775      │
│                                         │              │ Calamity Relief:      32      │
├─────────────────────────────────────────┼──────────────┼───────────────────────────────┤
│ Master Administrative Lookups (3 CSVs)  │     836 rows │ Master States:        36      │
│                                         │              │ Master Districts:    796      │
│                                         │              │ Master Tenures:        4      │
├─────────────────────────────────────────┼──────────────┼───────────────────────────────┤
│ TOTAL RAW CSV ROWS ACROSS 15 FILES      │ 395,871 rows │ Exact physical row sum        │
├─────────────────────────────────────────┼──────────────┼───────────────────────────────┤
│ Scheme Aggregate Benchmark (1 JSON)     │       5 keys │ Portal summary counters (Δ=0) │
└─────────────────────────────────────────┴──────────────┴───────────────────────────────┘
```
- **395,871 total rows** across the 15 immutable CSV files in `data/`.
- **395,035 rows** represent project-level, financial, and MP lifecycle transactions.
- **836 rows** represent geographic and parliamentary reference lookup tables.

### 1.3 Strict Governance Constraints
1. **Specification Only:** This document defines entities, keys, relations, and semantic rules. No implementation code for the analytical engine, anomaly detectors, risk scoring, ML models, REST APIs, frontend interfaces, or databases is introduced in this phase.
2. **First-Party Source Immutability:** All source definitions derive from the frozen 15 CSV files and 1 JSON summary extracted from the MoSPI e-SAKSHI portal. Raw data files remain strictly read-only and immutable.
3. **Epistemic Discipline:** Absence of downstream records (e.g., sanction, payment, completion) must never be conflated with administrative rejection, project cancellation, contractor abandonment, or financial wrongdoing. Every data-quality condition is assigned a deterministic analytical handling rule (flag, exclusion, or uncertainty marker).

---

## 2. Canonical Work Definition

### 2.1 Conceptual Distinction: Core Work Record vs. Child Observations
A critical architectural principle governs the MPLADS analytical model:
> **The Canonical Work is the core identity and administrative context record (Chamber, Sequence ID, Letter No, MP, Geography, Category, Description). Lifecycle milestone observations (Recommendation, Sanction, Completion, Expenditures, Attachments) remain separate child entities linked via relational keys.**

The analytical model must **never flatten multi-voucher expenditures, multiple attachments, or stage-specific metadata into a single monolithic table**. The Work table acts as the unifying spine, while individual payments and milestone events maintain their native cardinality.

### 2.2 Canonical Work Attribute Specifications

The canonical Work entity consolidates core contextual attributes across seven structural dimensions. All lifecycle milestones, financial disbursements, and completion events are preserved as child records:

| Attribute Dimension | Canonical Field Name | Source Field(s) | Source Dataset(s) | Datatype | Req / Opt | Source / Derived | Semantic Meaning & Analytical Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Identity** | `HOUSE_OF_PARLIAMENT` | `HOUSE_OF_PARLIAMENT` | All Datasets | `TINYINT` | **Required** | Source-Observed | Legislative chamber namespace: `1` = Rajya Sabha, `2` = Lok Sabha. |
| | `WORK_RECOMMENDATION_DTL_ID` | `WORK_RECOMMENDATION_DTL_ID` | Recommended, Sanctioned, Completed, Expenditures | `BIGINT` | **Required** | Source-Observed | Core sequential detail identifier assigned by government backend. |
| | `LETTER_NO` | `LETTER_NO` | Recommended, Sanctioned, Completed, Expenditures | `VARCHAR(128)` | **Required** | Source-Observed | Formal MP dispatch letter reference number (serves as sequence disambiguator). |
| | `ACTIVITY_NAME` | `ACTIVITY_NAME` | Recommended, Sanctioned, Completed, Expenditures | `VARCHAR(512)` | **Required** | Source-Observed | Standardized catalog activity code and short title (e.g., `WS/MP18398/2026-2027/...`). |
| **2. Sponsoring MP** | `MP_NAME` | `MP_NAME` | All Datasets | `VARCHAR(128)` | **Required** | Source-Observed | Legal name and term label of the sponsoring MP (descriptive identifier; not a pseudo-key). |
| **3. House & Tenure** | `TENURE` | `TENURE` | All Datasets | `VARCHAR(64)` | **Required** | Source-Observed | Parliamentary term category (e.g., `18th Lok Sabha`, `Sitting MP`, `Nominated`). |
| | `TENURE_START_DATE` | `TENURE_START_DATE` | All Work & MP Datasets | `TIMESTAMP` | **Required** | Source-Observed | Official commencement timestamp of MP's parliamentary tenure. |
| | `TENURE_END_DATE` | `TENURE_END_DATE` | All Work & MP Datasets | `TIMESTAMP` | **Required** | Source-Observed | Scheduled expiration timestamp of MP's parliamentary tenure. |
| **4. Geography** | `STATE_NAME` | `STATE_NAME` | All Datasets | `VARCHAR(64)` | **Required** | Source-Observed | State or Union Territory governing the project location. |
| | `CONSTITUENCY_ID` | `CONSTITUENCY_ID` | Recommended, Sanctioned, Completed, Allocations | `INT` | **Required** | Source-Observed | Parliamentary constituency code (1–543 for Lok Sabha; 545 Sitting RS; 546 Nominated RS). |
| | `CONSTITUENCY` | `CONSTITUENCY` | Recommended, Sanctioned, Completed, Allocations | `VARCHAR(128)` | **Required** | Source-Observed | Name of the Parliamentary Constituency or Rajya Sabha category. |
| | `IDA_NAME` | `IDA_NAME` | Recommended, Sanctioned, Completed, Expenditures | `VARCHAR(128)` | **Required** | Source-Observed | Implementing District Authority (District Magistrate, Collector, or Deputy Commissioner). |
| **5. Category** | `WORK_CATEGORY` | `WORK_CATEGORY` | Recommended, Sanctioned, Completed | `VARCHAR(64)` | **Required** | Source-Observed | Regulatory project category (`Normal/Others`, `Repair and Renovation`, `Trust and Society`). |
| **6. Description** | `WORK_DESCRIPTION` | `WORK_DESCRIPTION` | Recommended, Sanctioned, Completed | `TEXT` | Optional (0.1% null) | Source-Observed | Free-text technical project scope, site address, and specifications entered by MP staff. |
| **7. Workflow Stage**| `WORK_STAGE` | `WORK_STAGE` | Recommended, Sanctioned | `VARCHAR(64)` | Optional (0.5% null in Rec) | Source-Observed | **Observed workflow stage label** (`Pending for Sanction`, `Sanction`, `Vendor Identification`). |

*Rule against Field Invention:* No hypothetical fields (such as GPS coordinates, milestone progress percentages, contractor bids, or SC/ST quota indicators) may be added to the canonical Work model, as their absence from e-SAKSHI was empirically proven in Phase 0.

---

## 3. Canonical Work Identity & Entity Representation

### 3.1 Hierarchical Work Identity Architecture
To ensure conceptual integrity across all lifecycle stages while preserving raw data faithfully, the analytical engine formalizes a strict 4-tier identity hierarchy:

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

### 3.2 Key Formulation and Cross-Table Propagation

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

#### How Disambiguation and Child Linkage Work in Practice:
- **Sanction Linkage:** Across all 46 collision cases, exactly one of the two recommendations was ever sanctioned (in 100% of cases, the modern `WS/MP...` record). The legacy `NA-` record was never sanctioned. Therefore, in `Works Sanctioned`, each `(HOUSE, WORK_RECOMMENDATION_DTL_ID)` is already strictly unique.
- **Expenditure & Completion Linkage:** Because sanctions are 100% unique on `(HOUSE, WORK_RECOMMENDATION_DTL_ID)`, all downstream child tables (`Expenditures`, `Completed`) join to the sanctioned Work directly via `(HOUSE_OF_PARLIAMENT, WORK_RECOMMENDATION_DTL_ID)`.
- **Propagation of `LETTER_NO`:** While `LETTER_NO` is observed across all four main tables (`Recommended`, `Sanctioned`, `Completed`, `Expenditures`), its operational role in joins is as a qualification guard. For analytical storage, the Work entity assigns:
  $$\mathbf{K}_{\text{work}} = \text{HOUSE\_OF\_PARLIAMENT} \;\|\; \text{WORK\_RECOMMENDATION\_DTL\_ID} \;\|\; \text{LETTER\_NO}$$
  where `LETTER_NO` distinguishes the 46 un-sanctioned legacy recommendation rows from their modern counterparts.


### 3.3 Evaluation of Other Identifiers
- `ACTIVITY_NAME`: Informative descriptive string embedding `WORK_RECOMMENDATION_DTL_ID` in modern records, but legacy migrated records (`NA-`) lack consistent structure.
- `MP_NAME`: **Descriptive identifier only.** See Section 3.5.

### 3.4 Why `WORK_ID` Must NOT Be Used as a Universal Cross-Stage Key
A critical trap in naive e-SAKSHI data integration is attempting to use `WORK_ID` as a primary key. Phase 0 established that **`WORK_ID` must never be used as a cross-stage join key**:

1. **Datatype Incompatibility:**
   - In `Completed` tables, `WORK_ID` is an `int64` sequence (e.g., `148495`).
   - In `Expenditure` tables, `WORK_ID` is a formatted `str` (e.g., `WS/MP18275/2025-2026/243454`).
2. **Semantic Divergence:**
   - In `Completed`, `WORK_ID` is an internal asset inventory register counter unique only to the completion dataset.
   - In `Expenditure`, `WORK_ID` is a composite activity code whose trailing numeric token corresponds to `WORK_RECOMMENDATION_DTL_ID`, not the completion counter.
3. **Zero Join Success Rate:**
   - Directly joining `Completed` to `Expenditures` on `WORK_ID` produces **exactly 0.00% matches (0 / 45,704)**.
4. **Complete Absence in Upstream Stages:**
   - Neither `Works Recommended` (`FLAG: 1`) nor `Works Sanctioned` (`FLAG: 2`) contains a `WORK_ID` column. Any pipeline attempting to key projects by `WORK_ID` cannot represent the 135,078 recommendations or 101,511 sanctions.

### 3.5 MP Representation: Avoiding Dangerous Pseudo-IDs
Earlier exploratory proposals considered creating an artificial MP primary key by stripping punctuation or regex-normalizing `MP_NAME`. **This approach is explicitly rejected as unsafe**:
- Names are descriptive textual labels, not guaranteed entity identifiers.
- String normalization (e.g., merging `"A.B. Singh"` and `"AB Singh"`, or stripping honorifics) risks merging two distinct individuals or misattributing constituency tenures.
- **Definitive Phase 1 Rule:**
  > **MP identity is represented using source-provided MP name + House + tenure, with name treated as a descriptive identifier rather than a guaranteed government primary key.**
  
The analytical engine groups parliamentary data by `(HOUSE_OF_PARLIAMENT, MP_NAME, TENURE)` verbatim as recorded by MoSPI. Without an official external parliamentarian ID (such as a Digital Sansad member code), no synthetic pseudo-ID will be generated.

---

## 4. Lifecycle Model: Execution with Parallel Event Streams

### 4.1 Structural Lifecycle Architecture
The MPLADS project lifecycle is not a purely sequential linear conveyor belt where expenditure must precede completion. Rather, once a project receives administrative sanction, it enters the **Execution** phase. During execution, two asynchronous streams of observations occur:
1. **Expenditure Events:** A stream of zero, one, or multiple payment voucher debits released to commercial vendors ($0..N$).
2. **Completion Milestone:** A single formal handover event certifying physical completion ($0..1$).

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
┌─────────────────────────────────────────┐
│     3. EXECUTION / CURRENT STAGE        │ ──► Active administrative execution
│       (Observed WORK_STAGE label)       │
└─────────────┬───────────────────────────┘
              │
              ├───► Expenditure Events (0..N)
              │     [111,935 payment vouchers across 73,448 works]
              │     - Initial advances, material supplies, running bills
              │
              └───► Completion Milestone (0..1)
                    [45,704 completed assets with handover dates]
                    - 45,605 completed works have matching expenditure records
                    - 99 completed works have no expenditure records in snapshot
```

### 4.2 Lifecycle Semantics & Operational Rules
1. **`No Expenditure ≠ Execution Has Not Begun`:**
   A sanctioned work with zero expenditure records (`TOTAL_DISBURSED_AMT IS NULL`) may be under active physical construction, with invoices pending submission, verification, or treasury clearance. The analytical engine must **never assume execution is stalled or uninitiated solely because no payment voucher has been recorded**.
2. **`No Completion Record ≠ Stalled Work`:**
   55,807 sanctioned works have no completion record (`FLAG: 3`). A project sanctioned recently is progressing normally within its standard timeline.
3. **`No Sanction Record ≠ Rejected Work`:**
   34,182 recommendations lack a sanction row. Because e-SAKSHI exposes no public rejection table, these remain classified as `RECOMMENDED_UNSANCTIONED`.
4. **The 99 Completed Works with No Recorded Payment:**
   Phase 0 empirically identified 99 completed works (77 in Lok Sabha, 22 in Rajya Sabha) that have valid completion dates and amounts, but zero matching expenditure records in the scraped dataset.
   - **Epistemic Treatment:** The underlying administrative cause is unobserved and unresolved from portal records alone.
   - **Handling:** These records are preserved as valid completed works. The engine must **not** hypothesize unverified explanations (such as scheme convergence or offline payments).

### 4.3 `WORK_STAGE`: Observed Workflow Label vs. State Machine
In source datasets, `WORK_STAGE` is an **observed point-in-time administrative label** (e.g., `Pending for Sanction`, `Sanction`, `Vendor Identification`).
- e-SAKSHI does not publish a state transition history, event timestamp log, or transition validation table for this field.
- Phase 1 defines `WORK_STAGE` strictly as an **observed workflow stage label**, not a verified state machine.
- Downstream derived lifecycle states represent a synthesis of multiple observed records (`FLAG`, `SANCTION_DATE`, vouchers, `ACTUAL_END_DATE`), rather than relying solely on the text of `WORK_STAGE`.

---

## 5. Entity Relationship Model

The analytical foundation defines 11 distinct entities organized to preserve native cardinalities:

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

### 5.1 Formal Relationship Specifications

| Parent Entity | Child Entity | Cardinality | Relational Join Key | Direct / Inferred | Known Limitations & Handling |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MP / Tenure** | **Allocation** | $1 \rightarrow 1$ | `(HOUSE_OF_PARLIAMENT, MP_NAME, TENURE)` | Directly Observed | 5 Lok Sabha MPs and 33 Rajya Sabha MPs have 0 allocation rows in snapshot. |
| **MP / Tenure** | **Calamity Consent** | $1 \rightarrow \text{Many}$ | `(HOUSE_OF_PARLIAMENT, MP_NAME)` | Directly Observed | Sparse dataset (32 total records nationally). |
| **MP / Tenure** | **Work** | $1 \rightarrow \text{Many}$ | `(HOUSE_OF_PARLIAMENT, MP_NAME)` | Directly Observed | Sponsoring MP names match across 100.0% of works. |
| **Work** | **Recommendation** | $1 \rightarrow 1$ (Opt.) | `(HOUSE, DTL_ID, LETTER_NO)` | Directly Observed | 615 orphan sanctions lack recommendation entity. |
| **Work** | **Sanction** | $1 \rightarrow 1$ (Opt.) | `(HOUSE, DTL_ID)` | Directly Observed | 33,567 recommendations lack sanction entity (pending). Validated by empirical downstream uniqueness. |
| **Work** | **Completion** | $1 \rightarrow 1$ (Opt.) | `(HOUSE, DTL_ID)` | Directly Observed | 45,704 completed assets; 55,807 sanctioned works without an observed completion record. Zero orphan completions. Validated by empirical downstream uniqueness. |
| **Work** | **Expenditure** | $1 \rightarrow \text{Many}$ (Opt.)| `(HOUSE, DTL_ID)` | Directly Observed | **Preserve 1:M relationship.** Multiple payment vouchers per work are never flattened. Validated by empirical downstream uniqueness. |
| **Expenditure** | **Vendor** | $\text{Many} \rightarrow 1$ | `VENDOR_ID` | Directly Observed | 30,839 unique vendors mapped across 111,935 vouchers. 0% nulls. |
| **Expenditure** | **Implementing Agency**| $\text{Many} \rightarrow 1$ | `IA_NAME` | Directly Observed | 7,378 distinct IAs mapped. Observed exclusively on works with payments. |
| **Work / Completion**| **Attachment**| $1 \rightarrow \text{Many}$ (Opt.)| `ATTACH_ID` | Directly Observed | 67.77% null in Sanctions; 26.16% null in Completions. |


---

## 6. Financial Semantics & Aggregation Invariants

### 6.1 Field Definitions & Empirical Interpretations

| Financial Field | Exact Schema Definition | Entity Level | Semantic Interpretation | Operational Boundary |
| :--- | :--- | :--- | :--- | :--- |
| `RECOMMENDED_AMOUNT` | Estimated project cost in INR entered by MP staff upon proposal. | Recommendation | **Proposed Amount:** Initial budget request; unvetted by engineering estimates. | Advisory proposal value. |
| `SANCTION_AMOUNT` | Financial allocation recorded on the sanction record. | Sanction (Work) | **Sanctioned Amount:** Approved expenditure limit authorized by District Authority. | Upper ceiling for work disbursement vouchers. |
| `ACTUAL_AMOUNT` | Financial cost recorded in the completion record in INR. | Completion | **Completion-Record Amount:** Declared final expenditure upon asset handover. | Baseline for cost drift analysis. 97 records exhibit `0.00`. |
| `FUND_DISBURSED_AMT` | Exact monetary disbursement released in a single payment voucher. | Expenditure (Voucher)| **Individual Payment Amount:** Line-item payment voucher released to vendor. | Atomic transaction value. |
| `TOTAL_DISBURSED_AMT` | Sum of vouchers: $\sum \text{FUND\_DISBURSED\_AMT}$ where vouchers exist. | Work (Aggregated) | **Aggregate Observed Disbursement:** Cumulative funds disbursed against a work. | `NULL` if no vouchers observed (see Section 6.3). |
| `ALLOCATED_AMT` | Cumulative spending ceiling credited to an MP's parliamentary account. | MP / Tenure | **MP Allocation:** Entitlement limit (typically ₹5 Crore/year). | Statutory ceiling for MP's gross recommendations. |
| `CONSENTED_AMOUNT` | Amount surrendered by MP for declared natural calamities. | Calamity Consent | **Disaster Relief Surrender:** Quota transfer deducted from annual entitlement. | Sub-allocation subject to scheme guidelines. |

### 6.2 Strict Financial Aggregation Invariants

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FINANCIAL ADDITIVE SAFETY MATRIX                              │
├──────────────────────┬─────────────┬─────────────┬─────────────┬─────────────┬──────────────────┤
│ Financial Field      │ Work Level  │ MP Level    │ Dist Level  │ State Level │ National Level   │
├──────────────────────┼─────────────┼─────────────┼─────────────┼─────────────┼──────────────────┤
│ FUND_DISBURSED_AMT   │ SAFE (Sum)  │ SAFE (Sum)  │ SAFE (Sum)  │ SAFE (Sum)  │ SAFE (₹41.18B)   │
│ SANCTION_AMOUNT      │ ATOMIC      │ SAFE (Sum)* │ SAFE (Sum)* │ SAFE (Sum)* │ SAFE (Sum)*      │
│ RECOMMENDED_AMOUNT   │ ATOMIC      │ SAFE (Sum)* │ SAFE (Sum)* │ SAFE (Sum)* │ SAFE (Sum)*      │
│ ACTUAL_AMOUNT        │ ATOMIC      │ SAFE (Sum)* │ SAFE (Sum)* │ SAFE (Sum)* │ SAFE (Sum)*      │
│ ALLOCATED_AMT        │ INVALID     │ ATOMIC      │ INVALID     │ SAFE (Sum)  │ SAFE (₹117.00B)  │
│ CONSENTED_AMOUNT     │ INVALID     │ SAFE (Sum)  │ SAFE (Sum)  │ SAFE (Sum)  │ SAFE (Sum)       │
└──────────────────────┴─────────────┴─────────────┴─────────────┴─────────────┴──────────────────┘
  * Summation is mathematically valid ONLY over deduplicated Work entities.
```

#### The Three Core Aggregation Prohibitions:
1. **PROHIBITION 1: Never Sum `SANCTION_AMOUNT` Across Joined Expenditure Records.**  
   If a project has 5 payment vouchers, joining Sanctions to Expenditures replicates `SANCTION_AMOUNT` across all 5 rows. Summing `SANCTION_AMOUNT` on this joined set multiplies the approved liability by 5. `SANCTION_AMOUNT` must be summed strictly across unique Work entities.
2. **PROHIBITION 2: Never Sum `ACTUAL_AMOUNT` After Joining Completion to Expenditure.**  
   Joining Completion records to Expenditure vouchers replicates `ACTUAL_AMOUNT` across every voucher row. If a completed work has 5 payment vouchers, summing `ACTUAL_AMOUNT` across those joined rows produces 5 copies of the completion cost. `ACTUAL_AMOUNT` must be summed strictly across unique completed Work entities.
3. **PROHIBITION 3: Never Sum `ALLOCATED_AMT` Across Work Records.**  
   `ALLOCATED_AMT` is an MP-level entitlement balance. Summing it across works multiplies the MP's quota by the number of recommended works.

### 6.3 Reconciling `TOTAL_DISBURSED_AMT` with Missing Data Semantics
To prevent contradictions with the principle that *no expenditure record $\ne$ zero expenditure*:
- When a work has **zero observed payment vouchers**, the engine sets:
  $$\text{TOTAL\_DISBURSED\_AMT} = \mathbf{NULL}$$
  $$\text{HAS\_EXPENDITURE} = \mathbf{FALSE}$$
- `TOTAL_DISBURSED_AMT = 0.00` is assigned **only** when an analytical metric explicitly defines its scope as "observed cash flow disbursed through e-SAKSHI."
- Downstream detectors (e.g., fund dormancy, utilization ratios) must explicitly specify whether they treat unobserved expenditures as $0.00$ or as missing/inapplicable.

---

## 7. Temporal Semantics

### 7.1 Source Date Milestones
All dates in the e-SAKSHI corpus represent administrative or financial milestones recorded during scheme execution:

| Source Date Field | Dataset | Native Format | Coerced Canonical Datatype | Semantic Operational Meaning |
| :--- | :--- | :--- | :--- | :--- |
| `RECOMMENDATION_DATE`| Recommended | `DD-Mon-YYYY` | `DATE (ISO 8601)` | Date the sponsoring MP formally dispatched the project proposal. |
| `SANCTION_DATE` | Sanctioned | `DD-Mon-YYYY` | `DATE (ISO 8601)` | Date District Authority recorded administrative/financial sanction. |
| `EXPENDITURE_DATE` | Expenditures | `DD-Mon-YYYY` | `DATE (ISO 8601)` | Date payment voucher was authorized and debited in the portal. |
| `ACTUAL_END_DATE` | Completed | `DD-Mon-YYYY` | `DATE (ISO 8601)` | Date physical asset completion was recorded on the portal. |
| `TENURE_START_DATE` | All Datasets | `Mon DD, YYYY HH:MM:SS` | `TIMESTAMP` | Official commencement date of sponsoring MP's parliamentary tenure. |
| `TENURE_END_DATE` | All Datasets | `Mon DD, YYYY HH:MM:SS` | `TIMESTAMP` | Scheduled expiration date of sponsoring MP's parliamentary tenure. |

### 7.2 Empirical Temporal Integrity Finding
Phase 0 proved that when partitioned by chamber (`HOUSE_OF_PARLIAMENT`) and letter number (`LETTER_NO`), the entire national dataset exhibits **strictly monotonic temporal progression with exactly ZERO (0) sequence contradictions**:
- $\text{RECOMMENDATION\_DATE} \le \text{SANCTION\_DATE}$ (0 violations across 100,896 pairs)
- $\text{SANCTION\_DATE} \le \text{EXPENDITURE\_DATE}$ (0 violations across 111,935 vouchers)
- $\text{SANCTION\_DATE} \le \text{ACTUAL\_END\_DATE}$ (0 violations across 45,704 completed works)

### 7.3 Canonical Derived Temporal Intervals
The analytical engine defines five standard temporal intervals (durations in calendar days):

```text
       RECOMMENDATION_DATE
                │
                │  DAYS_TO_SANCTION
                ▼
          SANCTION_DATE
                │
                ├──────────────────────────────────────┐
                │  DAYS_TO_FIRST_PAYMENT               │  DAYS_TO_COMPLETION
                ▼                                      ▼
      FIRST_EXPENDITURE_DATE                   ACTUAL_END_DATE
                │                                      │
                │  PAYMENT_SPAN_DAYS                   │  DAYS_COMPLETION_TO_FINAL_PAYMENT
                ▼                                      ▼
       FINAL_EXPENDITURE_DATE ◄────────────────────────┘
```

1. **Recommendation-to-Sanction Latency (`DAYS_TO_SANCTION`):**
   $$\Delta t_{\text{sanc}} = \text{SANCTION\_DATE} - \text{RECOMMENDATION\_DATE}$$
2. **Sanction-to-First-Payment Latency (`DAYS_TO_FIRST_PAYMENT`):**
   $$\Delta t_{\text{pay1}} = \min(\text{EXPENDITURE\_DATE}) - \text{SANCTION\_DATE}$$
3. **Sanction-to-Completion Duration (`DAYS_TO_COMPLETION`):**
   $$\Delta t_{\text{compl}} = \text{ACTUAL\_END\_DATE} - \text{SANCTION\_DATE}$$
4. **Completion-to-Final-Payment Latency (`DAYS_COMPLETION_TO_FINAL_PAYMENT`):**
   $$\Delta t_{\text{pay\_post}} = \max(\text{EXPENDITURE\_DATE}) - \text{ACTUAL\_END\_DATE}$$
   *(Positive = post-handover voucher; Negative = final voucher released before completion record).*
5. **Payment Disbursement Span (`PAYMENT_SPAN_DAYS`):**
   $$\Delta t_{\text{span}} = \max(\text{EXPENDITURE\_DATE}) - \min(\text{EXPENDITURE\_DATE})$$

*Phase 0 Boundary:* No anomaly cutoffs or threshold flags are assigned to these durations in Phase 0. Threshold design, peer-group calibration, and baseline comparison belong strictly to Phase 1 (Baselines & Core Detection).

---

## 8. Missing Data Semantics

To prevent erroneous conclusions, the analytical engine enforces deterministic semantic rules for all six varieties of missing or unobserved data:

### 8.1 Taxonomy of Missingness

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MISSING DATA TAXONOMY & TREATMENT                         │
├──────────────────────────┬─────────────────────────────────┬───────────────────────────┤
│ Condition Category       │ Empirical Grounding in e-SAKSHI │ Analytical Engine Action  │
├──────────────────────────┼─────────────────────────────────┼───────────────────────────┤
│ 1. Null Value            │ Attribute missing in row        │ Preserve SQL NULL         │
│ 2. Absent Child Record   │ Downstream stage not observed   │ Outer join; set flag      │
│ 3. Not Applicable        │ Schema field irrelevant to entity│ Populate semantic sentinel│
│ 4. Not Yet Occurred      │ Event pending in real world     │ Open milestone status     │
│ 5. Unobserved in Snapshot│ Exists offline/un-scraped       │ Bound analytical claim    │
│ 6. Contradictory Record  │ Mismatched cross-stage values   │ Retain + Data-Quality flag│
└──────────────────────────┴─────────────────────────────────┴───────────────────────────┘
```

### 8.2 Grounded Case Rules

#### Rule 1: `No Sanction Record ≠ Rejected Work`
- **Empirical Reality:** 34,182 recommendation records have no matching sanction row.
- **Semantic Meaning:** e-SAKSHI does not expose a public rejection log. The work may be under active technical scrutiny by the District Authority, awaiting administrative clearance, or pending revised cost estimates.
- **Engine Handling:** Assign `LIFECYCLE_STAGE = 'RECOMMENDED_UNSANCTIONED'`. Do **not** classify as rejected, dropped, or delinquent.

#### Rule 2: `No Expenditure Record ≠ Zero Expenditure`
- **Empirical Reality:** 28,063 sanctioned works have no corresponding records in the expenditure dataset.
- **Semantic Meaning:** Physical work may be underway with contractor billing pending, or payment vouchers may be undergoing district treasury clearance.
- **Engine Handling:** Assign `TOTAL_DISBURSED_AMT = NULL` and `HAS_EXPENDITURE = FALSE`. Do **not** classify as an abandoned project or financial default.

#### Rule 3: `No IA_NAME ≠ Missing Implementing Agency in All Cases`
- **Empirical Reality:** `IA_NAME` is observed exclusively in the `Expenditures` dataset. Works that have not reached payment have no `IA_NAME` recorded in the public API.
- **Semantic Meaning:** An Implementing Agency is assigned under scheme guidelines during administrative sanction, but e-SAKSHI surfaces the agency name only within the expenditure module.
- **Engine Handling:** For sanctioned works without payments, preserve entity identity integrity by setting `IA_NAME = NULL` and assigning `IA_OBSERVATION_STATUS = 'NOT_OBSERVED_PRE_PAYMENT'`. Missingness metadata must not be stored as an entity value (which would corrupt downstream agency grouping and vendor-agency pairing analyses). Do **not** flag as administrative failure to assign an agency.

#### Rule 4: `No Completion Record ≠ Stalled Work`
- **Empirical Reality:** 55,807 sanctioned works have no completion record (`FLAG: 3`).
- **Semantic Meaning:** Projects take time to construct. A work sanctioned recently without a completion record is progressing normally within its standard timeline.
- **Engine Handling:** Assign `COMPLETION_STATUS = 'INCOMPLETE'`. Evaluate delay strictly relative to `SANCTION_DATE` and the snapshot timestamp, never purely on the absence of the completion record.

#### Rule 5: `Not Applicable (Nominated Rajya Sabha Constituency)`
- **Empirical Reality:** Nominated Rajya Sabha MPs have `CONSTITUENCY_ID = 546` and `CONSTITUENCY = 'Sitting Rajya Sabha'`.
- **Engine Handling:** Map `CONSTITUENCY_NAME = 'NOMINATED_STATEWIDE'`. Do **not** treat as missing geographic data.

---

## 9. Data-Quality Semantics

Known empirical edge cases identified in Phase 0 must be handled deterministically by later analytical stages without altering raw source data:

| Empirical Data-Quality Phenomenon | Observed Scope in Phase 0 | Root Cause / Inferred Mechanism | Analytical Engine Treatment | Exclusion / Flag / Uncertainty Marker |
| :--- | :--- | :--- | :--- | :--- |
| **Rajya Sabha Sequence Collisions** | 46 duplicate IDs across 92 rows in RS Rec | Sequence generator collision between legacy (`NA-`) and modern (`WS/MP...`) records. | Disambiguated by `LETTER_NO` in $\mathbf{K}_{\text{work}}$. | **Retained Source Data.** Key disambiguation resolves 100.0%. Both records preserved as distinct recommendations. |
| **Orphan Sanctions** | Exactly 615 sanctioned works lack recommendation row | Ingestion cutoff, disaster fast-track entry, or legacy migration gap. | Ingest into Work model with null recommendation attributes. | **Data-Quality Flag:** Set `FLAG_ORPHAN_SANCTION = TRUE`. Retained in sanction/expenditure analyses; excluded from recommendation-to-sanction delay metrics. |
| **Zero-Cost Completions** | Exactly 97 completed works exhibit `ACTUAL_AMOUNT == 0.00` | Administrative cancellation record, convergence financing, or clerical zero-entry. | Ingest verbatim as observed source record. | **Data-Quality Flag:** Set `FLAG_ZERO_COST_COMPLETION = TRUE`. Evaluated in cost-variance ratios as -1.0 (-100% variance relative to sanction); flagged for review to prevent misclassification as operational savings. |

| **Penny-Drop Banking Voucher** | Exactly 1 voucher has `FUND_DISBURSED_AMT == ₹0.01` | Automated bank account pre-validation check prior to bulk disbursement. | Ingest verbatim as observed payment record. | **Uncertainty Marker:** Set `FLAG_PENNY_DROP_PROBABLE = TRUE`. Retained in voucher counts; excluded from substantive vendor volume rankings. |
| **Missing Documentary Attachments** | 67.77% null in LS Sanctions; 26.16% null in LS Completed | Unassociated attachment records on portal. | Ingest `FILE_STATUS` and `ATTACH_ID` verbatim. | **Data-Quality Indicator:** Set `FLAG_DOCUMENT_ATTACHED = FALSE`. Evaluated strictly as an attachment-presence indicator, not proof of missing statutory certificates without payload inspection. |
| **Completed Works with Zero Payments** | Exactly 99 completed works lack expenditure records | Unobserved administrative reason (not established from portal data). | Retained in Completed model with `HAS_EXPENDITURE = FALSE`. | **Uncertainty Marker:** Retained as valid completed works; excluded from payment-timing metrics. |
| **Partial Lifecycle Coverage** | 101,511 sanctioned; 73,448 paid; 45,704 completed; 45,605 fully linked | Projects naturally reside at different operational stages along the multi-year pipeline. | Tag each work with an explicit lifecycle stage token. | **Analytical Stratification:** Engine stratifies analyses: 101k for sanctions, 73k for vendor patterns, 45.6k for end-to-end multi-stage profiling. |

---

## 10. Source vs. Derived Fields

To preserve clear boundaries between raw administrative evidence and computational metrics, the analytical engine maintains an explicit separation between source-observed and derived fields:

### 10.1 Source-Observed Fields (Raw e-SAKSHI Evidence)
These fields are ingested verbatim from the first-party API responses without transformation (other than datatype parsing):
- `WORK_RECOMMENDATION_DTL_ID`
- `LETTER_NO`
- `ACTIVITY_NAME`
- `WORK_DESCRIPTION`
- `WORK_CATEGORY`
- `WORK_STAGE`
- `RECOMMENDATION_DATE`
- `RECOMMENDED_AMOUNT`
- `SANCTION_DATE`
- `SANCTION_AMOUNT`
- `ACTUAL_END_DATE`
- `ACTUAL_AMOUNT`
- `FUND_DISBURSED_AMT`
- `EXPENDITURE_DATE`
- `WORK_STATUS`
- `VENDOR_ID`
- `VENDOR_NAME`
- `IA_NAME`
- `IDA_NAME`
- `MP_NAME`
- `HOUSE_OF_PARLIAMENT`
- `TENURE`
- `TENURE_START_DATE`
- `TENURE_END_DATE`
- `STATE_NAME`
- `CONSTITUENCY_ID`
- `CONSTITUENCY`
- `ALLOCATED_AMT`
- `CONSENTED_AMOUNT`
- `CALAMITY_NAME`
- `TYPE` (Calamity)
- `ATTACH_ID`
- `FILE_STATUS`
- `AVERAGE_RATING`

### 10.2 Derived Analytical Fields (Future Computational Metrics)
The following derived metrics will be computed by downstream analytical pipelines during Phase 1 (Core Detection) and Phase 2 (Cross-Work & Pattern Intelligence):

| Derived Field Name | Entity Level | Analytical Purpose | Mathematical Formula / Logical Definition | Input Field(s) | Treatment When Inputs Are Missing |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `WORK_KEY` | Work | Disambiguated primary key | `CONCAT(HOUSE_OF_PARLIAMENT, '_', WORK_RECOMMENDATION_DTL_ID, '_', LETTER_NO)` | `HOUSE_OF_PARLIAMENT`, `WORK_RECOMMENDATION_DTL_ID`, `LETTER_NO` | Inputs are mandatory; never null. |
| `HAS_EXPENDITURE` | Work | Payment occurrence flag | `CASE WHEN COUNT(Vouchers) > 0 THEN TRUE ELSE FALSE END` | Vouchers table | Deterministic boolean (`TRUE` / `FALSE`). |
| `TOTAL_DISBURSED_AMT` | Work | Cumulative disbursements | $\sum \text{FUND\_DISBURSED\_AMT}$ across vouchers for this work | `FUND_DISBURSED_AMT` | **Returns `NULL` if `HAS_EXPENDITURE = FALSE`.** |
| `VOUCHER_COUNT` | Work | Payment transaction count | $\text{COUNT}(\text{Voucher})$ across vouchers for this work | `FUND_DISBURSED_AMT` | If 0 vouchers exist, returns `0`. |
| `VENDOR_COUNT` | Work | Number of distinct vendors| $\text{COUNT}(\text{DISTINCT } \text{VENDOR\_ID})$ for this work | `VENDOR_ID` | If 0 vouchers exist, returns `0`. |
| `LIFECYCLE_STAGE` | Work | Stage categorization | `CASE WHEN FLAG=3 THEN 'COMPLETED' WHEN HAS_EXPENDITURE=TRUE THEN 'IN_PROGRESS_DISBURSING' WHEN SANCTION_DATE IS NOT NULL THEN 'SANCTIONED_UNPAID' ELSE 'RECOMMENDED_UNSANCTIONED' END` | `FLAG`, `SANCTION_DATE`, `HAS_EXPENDITURE` | Defaults to `'RECOMMENDED_UNSANCTIONED'`. |
| `FINANCIAL_UTILIZATION_RATIO` | Work | Sanction utilization rate | $\frac{\text{TOTAL\_DISBURSED\_AMT}}{\text{SANCTION\_AMOUNT}}$ | `TOTAL_DISBURSED_AMT`, `SANCTION_AMOUNT` | If `SANCTION_AMOUNT IS NULL`, `== 0`, or `TOTAL_DISBURSED_AMT IS NULL`, returns `NULL`. |
| `COST_VARIANCE_SANCTION_TO_REC` | Work | Sanction vs recommendation | $\frac{\text{SANCTION\_AMOUNT} - \text{RECOMMENDED\_AMOUNT}}{\text{RECOMMENDED\_AMOUNT}}$ | `SANCTION_AMOUNT`, `RECOMMENDED_AMOUNT` | If either is null or `RECOMMENDED_AMOUNT == 0`, returns `NULL`. |
| `COST_VARIANCE_ACTUAL_TO_SANC` | Work | Completion vs sanction | $\frac{\text{ACTUAL\_AMOUNT} - \text{SANCTION\_AMOUNT}}{\text{SANCTION\_AMOUNT}}$ | `ACTUAL_AMOUNT`, `SANCTION_AMOUNT` | If `SANCTION_AMOUNT IS NULL`, `== 0`, or `ACTUAL_AMOUNT IS NULL`, returns `NULL`. When `ACTUAL_AMOUNT == 0`, evaluates to `-1.0` (-100% variance) with `FLAG_ZERO_COST_COMPLETION = TRUE`. |
| `DAYS_TO_SANCTION` | Work | Recommendation to sanction | $\text{SANCTION\_DATE} - \text{RECOMMENDATION\_DATE}$ | `SANCTION_DATE`, `RECOMMENDATION_DATE` | If either date is null, returns `NULL`. |
| `DAYS_TO_FIRST_PAYMENT` | Work | Sanction to first voucher | $\min(\text{EXPENDITURE\_DATE}) - \text{SANCTION\_DATE}$ | `SANCTION_DATE`, `EXPENDITURE_DATE` | If either date is null, returns `NULL`. |
| `DAYS_TO_COMPLETION` | Work | Sanction to completion | $\text{ACTUAL\_END_DATE} - \text{SANCTION\_DATE}$ | `ACTUAL_END_DATE`, `SANCTION_DATE` | If either date is null, returns `NULL`. |
| `DAYS_COMPLETION_TO_FINAL_PAYMENT`| Work | Completion to final voucher| $\max(\text{EXPENDITURE\_DATE}) - \text{ACTUAL\_END_DATE}$ | `ACTUAL_END_DATE`, `EXPENDITURE_DATE` | If either date is null, returns `NULL`. |
| `PAYMENT_SPAN_DAYS` | Work | Disbursement duration | $\max(\text{EXPENDITURE\_DATE}) - \min(\text{EXPENDITURE\_DATE})$ | `EXPENDITURE_DATE` | If < 2 vouchers exist, returns `0`. |
| `HAS_ATTACHMENT` | Work | Attachment indicator | `CASE WHEN ATTACH_ID IS NOT NULL OR FILE_STATUS = 'True' THEN TRUE ELSE FALSE END` | `ATTACH_ID`, `FILE_STATUS` | Evaluates deterministically to `FALSE`. |
| `VENDOR_MARKET_SHARE_IDA` | Vendor | Vendor volume dominance within authority | $\frac{\sum \text{FUND\_DISBURSED\_AMT}_{\text{Vendor, IDA}}}{\sum \text{FUND\_DISBURSED\_AMT}_{\text{IDA}}}$ | `FUND_DISBURSED_AMT`, `VENDOR_ID`, `IDA_NAME` | Evaluated within Implementing District Authority (`IDA_NAME`) as the available administrative-district proxy (not a normalized census district ID); returns `NULL` if IDA total is 0. |


*Phase 0 Rule:* These derived fields are specified here for architectural alignment. They will not be calculated until Phase 1 and Phase 2 pipelines are executed.

---

## 11. Final Analytical Model

The resulting analytical architecture represents the complete domain model for the MPLADS Intelligence Engine:

```text
MP / Chamber Tenure (Descriptive: MP_NAME, HOUSE, TENURE)
  │
  ├── Allocation Ceiling (Entitlement balance, cumulative release)
  ├── Calamity Consent (Emergency surrenders: Kerala landslides, Punjab floods)
  │
  └── Canonical Work [WORK_KEY = (HOUSE, REC_DTL_ID, LETTER_NO)]
        │
        ├── Recommendation Event (Date, proposed amount, catalog activity, text description)
        ├── Sanction Event (Order date, approved ceiling, District Authority / IDA)
        ├── Execution State (Observed WORK_STAGE label)
        │
        ├── Expenditure Events [1:Many Vouchers]
        │     ├── Voucher Details (Transaction date, disbursed amount, payment status)
        │     ├── Assigned Vendor (VENDOR_ID, registered commercial name)
        │     └── Implementing Agency (IA_NAME, engineering/development division)
        │
        ├── Completion Event (Actual end date, recorded completion amount, citizen rating)
        │
        └── Supporting Attachments (ATTACH_ID group pointer to completion PDFs and site photos)
```

### 11.1 Key Structural Invariants
1. **Core Work vs. Milestone Events:** Canonical Work represents identity and contextual attributes; Recommendation, Sanction, Completion, Expenditures, and Attachments remain separate child entities preserving native cardinality.
2. **Atomic Payment Records:** Expenditures remain child records linked 1-to-many to the parent Work entity, preserving multi-vendor and multi-tranche execution histories.
3. **Execution as Parallel Streams:** Expenditures and completion represent asynchronous event streams occurring during execution, not a rigid sequential gate.
4. **Resilience to Missing Lifecycle Stages:** A Work entity gracefully models projects at any point in the pipeline (recommended-only, sanctioned-unpaid, active-disbursing, completed-unpaid, fully reconciled).

---

## 12. Phase 0 (Part 2) Definition of Done

The analytical foundation for the MPLADS Intelligence Engine is officially complete when all criteria below are verified:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   PHASE 0 (PART 2) DEFINITION OF DONE CHECKLIST                        │
├──────────────────────────────────────────────────────────────────┬─────────────────────┤
│ Criterion / Requirement                                          │ Status              │
├──────────────────────────────────────────────────────────────────┼─────────────────────┤
│ 1. Canonical Work definition covers core identity & context      │ VERIFIED (Sec 2)    │
│ 2. Canonical Work Key distinguishes source key from LETTER_NO    │ VERIFIED (Sec 3.1)  │
│ 3. Incompatibility of WORK_ID as cross-stage key is documented   │ VERIFIED (Sec 3.4)  │
│ 4. MP identity represented via descriptive attributes (no pseudo-ID)| VERIFIED (Sec 3.5)|
│ 5. Lifecycle models execution with parallel payment/completion   │ VERIFIED (Sec 4)    │
│ 6. Cardinality preserved for 1:M expenditures (never flattened)  │ VERIFIED (Sec 5)    │
│ 7. Financial semantics, limits, and additive safety established │ VERIFIED (Sec 6)    │
│ 8. Prohibits summing ACTUAL_AMOUNT across joined vouchers       │ VERIFIED (Sec 6.2)  │
│ 9. TOTAL_DISBURSED_AMT = NULL when no vouchers observed          │ VERIFIED (Sec 6.3)  │
│ 10. Temporal milestones and derived intervals formalized         │ VERIFIED (Sec 7)    │
│ 11. Missing-data taxonomy & grounded rules established           │ VERIFIED (Sec 8)    │
│ 12. 99 completed works with no payment stated without speculation│ VERIFIED (Sec 8.2)  │
│ 13. Data-quality treatment defined for all empirical edge cases  │ VERIFIED (Sec 9)    │
│ 14. Source-observed vs. derived fields strictly separated       │ VERIFIED (Sec 10)   │
│ 15. Final conceptual entity model finalized                     │ VERIFIED (Sec 11)   │
│ 16. Total row count defined with master/lifecycle breakdown      │ VERIFIED (Sec 1.2)  │
│ 17. Zero implementation code executed (Specification Only)      │ VERIFIED            │
└──────────────────────────────────────────────────────────────────┴─────────────────────┘
```

**Phase 0 Analytical Foundation is complete. No unresolved modeling ambiguity remains that would impede the Phase 0 Staging Pipeline or Phase 1 (Baselines & Core Detection).**
