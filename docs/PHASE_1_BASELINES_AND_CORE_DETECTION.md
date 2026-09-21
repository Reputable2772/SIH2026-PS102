# Phase 1 — Baselines & Core Detection Specification
**MPLADS Intelligence Engine (SIH PS102 Prototype)**  
**Authoritative Data Foundation:** [`PHASE_0_DATA_FOUNDATION.md`](PHASE_0_DATA_FOUNDATION.md) (Frozen Snapshot: 2026-09-21)  
**System Architecture Reference:** [`Core.md`](Core.md)  
**Document Status:** Formal Analytical Specification (Zero Implementation Code)  
**Phase Mapping:** Phase 1 of 4-Phase System Architecture  

---

## 1. Executive Summary & Phase 1 Mandate

### 1.1 Objective and Scope
Phase 1 establishes the first analytical intelligence layer of the MPLADS Intelligence Engine prototype. Building strictly upon the frozen empirical audit, canonical Work model, and relational foundations defined in [`PHASE_0_DATA_FOUNDATION.md`](PHASE_0_DATA_FOUNDATION.md), Phase 1 specifies the mathematical formulations, eligibility rules, baseline methodologies, detector contracts, validation matrix, and explainability standards for:

```text
Eligibility Filtering  →  Baseline Formulation  →  Core Anomaly Detection  →  Structured Finding Generation
```

Phase 1 covers three core anomaly families:
1. **Compliance Detection:** Procedural adherence and statutory/monitoring deviations relative to official scheme guidelines and ministerial benchmarks.
2. **Financial Anomaly Detection:** Cost estimation drift, sanction ceiling violations, and disbursement pacing irregularities.
3. **Execution & Timeline Detection:** Milestone duration tracking, elapsed execution age, and completion pacing signals.

### 1.2 Foundational Governance & Analytical Invariants
All Phase 1 detectors operate under strict epistemic and architectural constraints:

1. **Specification Only (Zero Implementation):** This document defines analytical mechanics, formulas, thresholds, and contracts. No Python scripts, detector code, ML models, APIs, frontend UI, or database pipelines are implemented in this phase.
2. **Non-Punitive Missing-Data Treatment:** Missing data is never treated as a negative finding or irregularity. A work lacking an observed completion record or payment voucher is evaluated strictly through formal eligibility gates; it is never assumed to be delinquent, physically abandoned, or fraudulent.
3. **Strict Epistemic Neutrality:** Detectors produce objective statistical and procedural findings. No detector may output a "fraud score", "corruption verdict", or assertion of intentional criminality or unobserved physical status. The engine outputs review-prioritization flags indicating operational deviations warranting administrative review.
4. **Preservation of Phase 0 Invariants:**
   - Work-level metrics are computed strictly at the unique canonical Work level (`K_work`); work-level amounts (`SANCTION_AMOUNT`, `ACTUAL_AMOUNT`) must **never** be summed across joined payment vouchers.
   - For unspent works, cumulative expenditure is mathematically `NULL`, not ₹0.00.
   - Zero-cost completions (97 records) represent valid observed records evaluating to `-1.0` (-100% variance relative to sanction), not missing values.
   - Sponsoring MP identity is treated as a descriptive tuple `(HOUSE_OF_PARLIAMENT, MP_NAME, TENURE)` without synthetic pseudo-keys.

---

## 2. Baseline Framework

An anomaly cannot exist in the abstract; it can only be quantified as a measured deviation from an authoritative baseline. Phase 1 establishes three distinct classes of comparison baselines:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        THREE-TIER BASELINE TAXONOMY                    │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Regulatory / Policy   │ Hard statutory mandates and ministerial     │
│    Baselines             │ administrative monitoring thresholds.       │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 2. Peer Group            │ Stratified cohort distributions of          │
│    Baselines             │ comparable public works across dimensions.  │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 3. Historical /          │ Longitudinal tenure baselines conditioned    │
│    Behavioural Baselines │ on post-2023 e-SAKSHI system coverage.      │
└──────────────────────────┴─────────────────────────────────────────────┘
```

### 2.1 Regulatory & Procedural Baselines
Regulatory baselines translate official statutory mandates and parliamentary monitoring criteria into deterministic comparison rules. Every rule is classified into one of three legal categories:

| Rule Identifier | Regulatory Classification | Target Milestone Interval | Statutory / Administrative Authority | Configured Baseline Value | Operational Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RB-01** | **Statutory Mandate** | Recommendation → Sanction | MPLADS Guidelines 2023, Para 3.2.4; Lok Sabha Question *44 | **45 Calendar Days** | District Authority must issue formal administrative sanction or communicate rejection within 45 days of receipt of MP proposal. |
| **RB-02** | **Official Monitoring Criterion** | Sanction → Completion | MPLADS Guidelines 2023, Para 3.2.12; Lok Sabha Question *44; Standing Committee Report 35 | **1 Calendar Year** (with legitimate terrain/civil exceptions) | Ministry of Statistics and Programme Implementation (MoSPI) monitoring threshold for non-completed sanctioned projects. |
| **RB-03** | **Official Monitoring Criterion** | Sanction → First Payment | e-SAKSHI System Benchmark; Lok Sabha Question *44 | **3 Calendar Months** | MoSPI monitoring threshold for fund dormancy: sanctioned works with zero payments within 3 months of sanction order. |
| **RB-04** | **Statutory Ceiling** | Cumulative Disbursements vs Sanction | MPLADS Guidelines 2023, Para 4.1 | SUM(Disbursements) ≤ Sanction | Treasury releases must never exceed approved administrative sanction amount. |
| **RB-05** | **Statutory Reference Baseline** | Emergency Calamity Surrender Limit | MPLADS Guidelines 2023, Para 5.1 | ≤ ₹1.00 Crore (Severe in country)<br>≤ ₹25.0 Lakh per annum (State affected area) | Sponsoring MP calamity consent surrenders cannot exceed statutory disaster ceilings. *(Reference baseline only; no dedicated Phase 1 detector).* |

> [!IMPORTANT]
> **Distinction Between Mandates, Exceptions, and Monitoring Benchmarks:**
> - `RB-01` (45 days) is a **statutory deadline** established by Para 3.2.4 of the published scheme guidelines.
> - `RB-02` (1 year, Para 3.2.12) is a **stipulated benchmark** (*"District Authority shall stipulate a completion period which should generally not exceed one year... in exceptional cases such as difficult/hilly terrain, more time may be allowed where justified"*). Exceeding 1 year triggers administrative monitoring review (`EXCEEDS_STANDARD_COMPLETION_WINDOW`), not an automatic procedural violation.
> - `RB-03` (3 months) is an **administrative monitoring criterion** officially tracked by MoSPI in parliamentary disclosures (Lok Sabha Starred Question No. *44 of 22-Jul-2026). Exceeding these windows triggers ministerial administrative review, not automatic legal culpability.
> - `RB-05` (Calamity Limits) is recorded as an authoritative reference baseline; calamity surrenders are MP-level allocation events evaluated during multi-work portfolio analysis in later phases.

### 2.2 Detector-Specific Peer Baselines
To evaluate civil timelines and financial metrics fairly, comparisons must be conditioned on appropriate operational dimensions. A single universal peer grouping is insufficient because cost variance, civil construction duration, and administrative sanction speed operate across distinct drivers:

1. **Financial & Cost Drift (D6):**
   - *Primary Dimensions:* `(WORK_CATEGORY, STATE_NAME, IDA_NAME)`
   - *Rationale:* Civil engineering costs, materials, and Schedule of Rates (SoR) vary heavily by work type, state policy, and district geography.
2. **Execution Duration & Timeline (D2):**
   - *Primary Dimensions:* `(WORK_CATEGORY, WORK_SUB_TYPE, STATE_NAME)`
   - *Rationale:* Project duration depends on technical civil requirements (e.g. major bridge vs solar lighting) and regional climatic/terrain constraints.
3. **Administrative Decision Delay (D1, D9):**
   - *Primary Dimensions:* `(IDA_NAME, STATE_NAME)`
   - *Rationale:* Administrative sanction speed reflects the capacity, backlog, and procedural throughput of the District Authority (`IDA_NAME`), independent of the physical work type.

#### Peer Group Construction Hierarchy & Fallback Architecture
Every detector constructs its peer cohort hierarchically using a 3-tier fallback architecture:

```text
Level 1: Fine-Grained Peer Group (Detector-Specific Primary Dimensions)
         ▼ (If Sample Size N < 30)
Level 2: Intermediate Peer Group (State Level Dimension)
         ▼ (If Sample Size N < 30)
Level 3: National Category Baseline (National Level Dimension)
```

#### Robust Non-Parametric Peer Metrics & Initial Analytical Defaults (Heuristics)
Because public procurement data is heavily skewed and contains legitimate high-cost outliers, peer baselines use **robust non-parametric statistics**. The numeric thresholds below are **initial analytical defaults (heuristics)** subject to ongoing empirical calibration during prototype validation, rather than universal mathematical constants:

- **Location Metric:** Median (\(\text{Median}(X) = P_{50}\))
- **Spread Metric:** Median Absolute Deviation (\(\text{MAD} = \text{median}(|X_i - \text{Median}(X)|)\)) or Interquartile Range (\(\text{IQR} = P_{75} - P_{25}\))
- **Outlier Multipliers (Heuristic Defaults):**
  \[
  \text{Upper Bound} = P_{75} + 1.5 \times \text{IQR} \quad (\text{Standard Outlier Heuristic})
  \]
  \[
  \text{Extreme Upper Bound} = P_{75} + 3.0 \times \text{IQR} \quad (\text{Extreme Outlier Heuristic})
  \]

#### Sample Size Thresholds and Fallback Rules (Configurable Defaults)
- **Sample Size for Robust Z-Score (\(N_{\text{min}} = 30\)):** Initial analytical heuristic default for robust central limit properties.
- **Sample Size for Basic Percentile Ranking (\(N_{\text{perc}} = 10\)):** Minimum heuristic sample to compute quartiles.
- **Sparse Cohort Rule (\(N < 10\)):** If even the national cohort has \(N < 10\), statistical deviation detection is **disabled** for that work, setting `evaluation_status = INSUFFICIENT_DATA`.
- **Transparency Marker:** When fallback occurs, the finding must explicitly flag `PEER_GROUP_FALLBACK_APPLIED = TRUE` and specify the active resolution level (`LEVEL_2_STATE` or `LEVEL_3_NATIONAL`).

### 2.3 Historical & Behavioural Baselines
Historical baselines analyze temporal submission patterns, seasonal fiscal-year surges, and parliamentary tenure transitions under four boundary invariants:

1. **The e-SAKSHI Temporal Horizon:** Comprehensive digital tracking in e-SAKSHI began w.e.f. 1st April 2023. Historical longitudinal baselines must **not** extend prior to April 2023.
2. **Tenure Boundary Partitioning:** Lok Sabha operates on 5-year general election cycles (18th Lok Sabha commenced June 2024); Rajya Sabha operates on staggered 6-year terms with biennial retirements. Sponsoring patterns cannot be concatenated across distinct terms without explicit tenure normalization.
3. **Snapshot Truncation Invariant:** The authoritative dataset is a point-in-time snapshot frozen on **2026-09-21**. Works initiated in recent months cannot be compared against historical full-year completion distributions.

---

## 3. Detector Eligibility Engine & Financial Aggregation Rules

### 3.1 Clean Separation of Evaluation Status, Finding Type, and Severity
To guarantee 100% architectural consistency across schemas, prose, and test fixtures:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      3-AXIS CONTRACT ARCHITECTURE                      │
├────────────────────────┬───────────────────────────────────────────────┤
│ 1. evaluation_status   │ EVALUABLE, NOT_YET_ELIGIBLE, INSUFFICIENT_DATA│
│                        │ DATA_QUALITY_CONFLICT, NOT_APPLICABLE         │
├────────────────────────┼───────────────────────────────────────────────┤
│ 2. finding_type        │ ANOMALY (Actionable review divergence),       │
│                        │ DATA_QUALITY (Observed empirical anomaly),    │
│                        │ INFORMATIONAL (Descriptive telemetry)         │
├────────────────────────┼───────────────────────────────────────────────┤
│ 3. severity            │ NORMAL, LOW, MEDIUM, HIGH                     │
│                        │ (No 'SPECIAL' status permitted)               │
└────────────────────────┴───────────────────────────────────────────────┘
```

- **`NOT_APPLICABLE` Policy:** If a detector stage is irrelevant to the target work's lifecycle state (e.g. cost completion drift for an incomplete work), `evaluation_status = NOT_APPLICABLE` and **no finding object is emitted** downstream.

### 3.2 Explicit Payment State Filtering Rule (Source Field Invariant)
The raw e-SAKSHI expenditure tables record payment-state telemetry under the **`WORK_STATUS`** column (with observed values `Payment Success` [107,639 records] and `Payment In-Progress` [4,296 records]).
To ensure financial fidelity:
- **Disbursement Aggregation Rule:** `TOTAL_DISBURSED_AMT` and individual voucher disbursements aggregate **strictly** records where:
  \[
  \text{WORK\_STATUS} == \text{'Payment Success'}
  \]
- Vouchers marked as `Payment In-Progress` remain valid raw source records capturing initiated payment workflows, but are **excluded** from successfully disbursed funds. They do not count toward cumulative expenditure or statutory disbursement ceiling checks (`RB-04`).

### 3.3 Eligibility Gating Matrix by Detector

| Detector ID | Detector Title | Target Stage | Required Prerequisite Fields | Ineligible / Gate Criteria | Handled As |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D1** | Sanction Delay | Recommendations & Sanctions | `RECOMMENDATION_DATE`, `SANCTION_DATE` | 1. Recommendation lacks sanction<br>2. Sanction lacks recommendation (615 orphan sanctions) | 1. Handled by D9<br>2. `DATA_QUALITY_CONFLICT` (`FLAG_ORPHAN_SANCTION`) |
| **D3_PAYMENT_INCEPTION** | First Payment Inception Delay | Sanctions & Expenditures | `SANCTION_DATE`, `EXPENDITURE_DATE` (`WORK_STATUS == 'Payment Success'`) | 1. Unspent works (0 successful vouchers)<br>2. Recommendation unsanctioned | 1. Handled by D3_PAYMENT_DORMANCY<br>2. `NOT_APPLICABLE` |
| **D3_PAYMENT_DORMANCY** | Fund Inactivity Dormancy | Sanctions & Expenditures | `SANCTION_DATE`, `SNAPSHOT_DATE` | 1. Sanctioned < 3 calendar months at snapshot date (11,369 works)<br>2. Work is completed with 0 payment records (99 works)<br>3. Work already has ≥ 1 successful payment | 1. `NOT_YET_ELIGIBLE`<br>2. `NOT_APPLICABLE` (`FLAG_COMPLETED_WITHOUT_VOUCHER = TRUE`)<br>3. `NOT_APPLICABLE` (Handled by Inception) |
| **D9** | Unsanctioned Dormancy| Recommendations | `RECOMMENDATION_DATE`, `SNAPSHOT_DATE` | 1. Work has already received sanction<br>2. Proposal < 45 days old at snapshot | 1. `NOT_APPLICABLE`<br>2. `NOT_YET_ELIGIBLE` |
| **D6** | Cost Drift (Rec → Sanc)| Recommendations & Sanctions | `RECOMMENDED_AMOUNT`, `SANCTION_AMOUNT` | 1. Recommendation unsanctioned<br>2. Orphan sanction (absent recommendation) | 1. `NOT_APPLICABLE`<br>2. `DATA_QUALITY_CONFLICT` |
| **D6** | Cost Drift (Sanc → Actual)| Sanctions & Completions | `SANCTION_AMOUNT`, `ACTUAL_AMOUNT` | 1. Work incomplete (`FLAG != 3`)<br>2. Sanction ceiling == 0 | 1. `NOT_APPLICABLE`<br>2. `INSUFFICIENT_DATA` |
| **D2** | Completion Timeline | Sanctions & Completions | `SANCTION_DATE`, `ACTUAL_END_DATE` | 1. Work incomplete & sanctioned ≤ 1 calendar year at snapshot<br>2. Work unsanctioned | 1. `NOT_YET_ELIGIBLE`<br>2. `NOT_APPLICABLE` |

---

## 4. Core Compliance Detectors

Compliance detectors evaluate procedural adherence against statutory guidelines and official ministerial monitoring criteria.

### 4.1 Detector D1 — Statutory Sanction Delay Detector

#### Analytical Objective
Identifies public works where the District Authority took longer than the statutory 45-day window to issue formal administrative sanction following receipt of the MP's proposal.

#### Regulatory Basis
MPLADS Guidelines 2023, Para 3.2.4: *"The District Authority shall sanction or reject the works recommended by the MP within 45 days from the receipt of the recommendation."* Reaffirmed in Lok Sabha Starred Question No. *44 of 22-Jul-2026.

#### Mathematical Formulation
```text
DAYS_TO_SANCTION = SANCTION_DATE - RECOMMENDATION_DATE
STATUTORY_EXCESS_DAYS = max(0, DAYS_TO_SANCTION - tau_sanction_window)
```
where \(\tau_{\text{sanction\_window}}\) is the configured statutory sanction window (default: 45 calendar days).

#### Population & Coverage
- **Eligible Population:** Matched recommendation-sanction pairs (**100,896 works**; 99.39% of sanctions).
- **Ineligible / Excluded:**
  - 33,567 pending proposals without sanction (evaluated under D9).
  - 615 orphan sanctions lacking recommendation dates (`DATA_QUALITY_CONFLICT`).
- **Temporal Contradictions:** Exactly 0 within-house inverted dates (`SANCTION_DATE < RECOMMENDATION_DATE` = 0).

#### Severity Calibration Matrix

| Severity Level | Observed Delay Interval | Logical Condition | Finding Type | Administrative Action Guidance |
| :--- | :--- | :--- | :--- | :--- |
| **NORMAL** | ≤ 45 calendar days | `DAYS_TO_SANCTION <= tau_sanction_window` | `INFORMATIONAL` | Compliant with statutory timeline. |
| **LOW** | 46 to 60 calendar days | `tau_sanction_window < DAYS_TO_SANCTION <= 60` | `ANOMALY` | Minor administrative delay (+1 to +15 days over limit). |
| **MEDIUM** | 61 to 90 calendar days | `60 < DAYS_TO_SANCTION <= 90` | `ANOMALY` | Moderate procedural delay (+16 to +45 days over limit). |
| **HIGH** | > 90 calendar days | `DAYS_TO_SANCTION > 90` | `ANOMALY` | Severe statutory delay (>2x statutory window; warranting audit). |

#### Evidence & Explanatory Output
- **Evidence Items:** `RECOMMENDATION_DATE`, `SANCTION_DATE`, computed `DAYS_TO_SANCTION`, `IDA_NAME`, configured statutory threshold \(\tau_{\text{sanction\_window}}\).
- **Standard Explanation Template:**
  > *"Work [WORK_KEY] sponsored by MP [MP_NAME] took [DAYS_TO_SANCTION] calendar days to receive administrative sanction from [IDA_NAME] (Recommended: [REC_DATE], Sanctioned: [SANC_DATE]). This exceeds the statutory 45-day decision window mandated by Para 3.2.4 of the MPLADS 2023 Guidelines by [STATUTORY_EXCESS_DAYS] days (Severity: [SEVERITY])."*

---

### 4.2 Detector D3 — Fund Inception & Dormancy Detectors (D3_PAYMENT_INCEPTION & D3_PAYMENT_DORMANCY)

To prevent conflating distinct operational states under one identifier, D3 is partitioned into two dedicated detectors:

#### 1. Detector D3_PAYMENT_INCEPTION (Paid Works)
- **Analytical Objective:** Evaluates historical delay in releasing the initial disbursement tranche.
- **Population:** Sanctioned works with \(\ge 1\) successful payment voucher (73,448 works).
- **Deadline:** \(\text{INCEPTION\_DEADLINE} = \text{SANCTION\_DATE} + \text{3 Calendar Months}\).
- **Formula:**
  ```text
  INCEPTION_DELAY_DAYS = min(EXPENDITURE_DATE) - SANCTION_DATE
  INCEPTION_OVERDUE_DAYS = max(0, min(EXPENDITURE_DATE) - INCEPTION_DEADLINE)
  ```

| Severity Level | Inception Delay Duration | Logical Condition | Finding Type | Administrative Meaning |
| :--- | :--- | :--- | :--- | :--- |
| **NORMAL** | ≤ 3 calendar months | `min(EXP_DATE) <= INCEPTION_DEADLINE` | `INFORMATIONAL` | Compliant first payment tranche release. |
| **LOW** | 3 to 6 calendar months | `0 < INCEPTION_OVERDUE_DAYS <= 90` | `ANOMALY` | Delayed inception: First payment released 3 to 6 months post-sanction. |
| **MEDIUM** | 6 to 12 calendar months | `90 < INCEPTION_OVERDUE_DAYS <= 275`| `ANOMALY` | Severe inception delay: First payment released 6 to 12 months post-sanction. |
| **HIGH** | > 12 calendar months | `INCEPTION_OVERDUE_DAYS > 275` | `ANOMALY` | Chronic inception delay: First payment released > 1 year post-sanction. |

#### 2. Detector D3_PAYMENT_DORMANCY (Unspent Incomplete Works)
- **Analytical Objective:** Identifies sanctioned incomplete works exhibiting zero financial releases beyond the official 3-month ministerial threshold.
- **Regulatory Basis:** MoSPI Lok Sabha Starred Question No. *44 (22-Jul-2026) monitoring criterion.
- **Deadline:** \(\text{DORMANCY\_DEADLINE} = \text{SANCTION\_DATE} + \text{3 Calendar Months}\).
- **Formula:**
  ```text
  SANCTION_AGE_DAYS = T_snapshot - SANCTION_DATE
  DORMANCY_EXCESS_DAYS = max(0, T_snapshot - DORMANCY_DEADLINE)
  ```
- **Population Split:**
  - 11,369 unspent incomplete works sanctioned < 3 months: `NOT_YET_ELIGIBLE`.
  - 99 completed works with 0 payments: `NOT_APPLICABLE` (`FLAG_COMPLETED_WITHOUT_VOUCHER = TRUE`).
  - 16,595 incomplete works aged \(\ge 3\) months: `EVALUABLE` under matrix below.

| Severity Level | Inactivity Duration from Sanction | Logical Condition | Finding Type | Administrative Finding |
| :--- | :--- | :--- | :--- | :--- |
| **NOT_YET_ELIGIBLE**| < 3 calendar months | `T_snapshot < DORMANCY_DEADLINE` | N/A | Mobilization window open; not eligible for dormancy flag. |
| **LOW** | 3 to 6 calendar months | `0 < DORMANCY_EXCESS_DAYS <= 90` | `ANOMALY` | Dormant: 3 to 6 months with no observed disbursement. |
| **MEDIUM** | 6 to 12 calendar months | `90 < DORMANCY_EXCESS_DAYS <= 275`| `ANOMALY` | Dormant: 6 to 12 months with no observed disbursement. |
| **HIGH** | > 12 calendar months | `DORMANCY_EXCESS_DAYS > 275` | `ANOMALY` | Severely Dormant: > 1 year post-sanction with no observed disbursement. |

---

### 4.3 Detector D9 — Unsanctioned Recommendation Dormancy Detector

#### Analytical Objective
Identifies formal MP proposals that have remained without administrative sanction or recorded administrative disposition well beyond statutory review windows.

#### Regulatory Basis
MPLADS Guidelines 2023, Para 3.2.4 (45-day review requirement) & e-SAKSHI Pending Proposal Backlog Register.

#### Epistemic Boundary
Pending proposals must **never** be classified as rejected, cancelled, or delinquent. e-SAKSHI does not expose a rejection log. Findings state neutrally that the proposal remains pending administrative review.

#### Mathematical Formulation
```text
PENDING_AGE_DAYS = T_snapshot - RECOMMENDATION_DATE
REVIEW_EXCESS_DAYS = max(0, PENDING_AGE_DAYS - tau_review_window)
Condition: LIFECYCLE_STAGE == 'RECOMMENDED_UNSANCTIONED'
```
where \(\tau_{\text{review\_window}}\) is the configured statutory review threshold (default: 45 calendar days).

#### Population & Coverage
- **Eligible Population:** 33,567 pending recommendation proposals.
- **Orphan Sanctions Excluded:** Exactly 615 orphan sanctions lack recommendation rows and are excluded (`NOT_APPLICABLE`).

#### Severity Calibration Matrix

| Severity Level | Pending Elapsed Duration | Logical Condition | Finding Type | Administrative Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **NORMAL** | ≤ 45 days | `PENDING_AGE_DAYS <= tau_review_window` | `INFORMATIONAL` | Active statutory review window. |
| **LOW** | 46 to 90 days | `tau_review_window < PENDING_AGE_DAYS <= 90` | `ANOMALY` | Moderate backlog: Proposal pending 1.5 to 3 months. |
| **MEDIUM** | 91 to 180 days | `91 <= PENDING_AGE_DAYS <= 180` | `ANOMALY` | Serious backlog: Proposal pending 3 to 6 months. |
| **HIGH** | > 180 days | `PENDING_AGE_DAYS > 180` | `ANOMALY` | Chronic backlog: Proposal pending > 6 months without order. |

---

## 5. Core Financial Detectors & Signals

### 5.1 Detector D6 — Cost Estimation & Sanction Drift Profiler

#### Analytical Objective & Finding Identity Disambiguation
Detects statistically abnormal cost escalations or severe de-escalations across project milestone stages.
To avoid finding collision and preserve clean architectural modeling, D6 uses a unified detector family with an explicit, mandatory `sub_detector_id`:
- `sub_detector_id = "REC_SANC"`: Recommendation \(\to\) Sanction Drift Ratio (\(\Delta_{\text{sanc\_rec}}\), evaluated across 100,896 works).
- `sub_detector_id = "SANC_ACTUAL"`: Sanction \(\to\) Actual Completion Drift Ratio (\(\Delta_{\text{act\_sanc}}\), evaluated across 45,704 works).

Each sub-detector finding has a unique deterministic finding identity:
\[
\text{finding\_id} = \text{SHA256}(\text{detector\_id} + \text{":"} + \text{sub\_detector\_id} + \text{":"} + \text{target\_work\_key} + \text{":"} + \text{target\_event\_key} + \text{":"} + \text{config\_hash})
\]

#### Mathematical Formulations
1. **Recommendation → Sanction Drift Ratio (`REC_SANC`):**
   \[
   \Delta_{\text{sanc\_rec}} = \frac{\text{SANCTION\_AMOUNT} - \text{RECOMMENDED\_AMOUNT}}{\text{RECOMMENDED\_AMOUNT}}
   \]
2. **Actual → Sanction Completion Drift Ratio (`SANC_ACTUAL`):**
   \[
   \Delta_{\text{act\_sanc}} = \frac{\text{ACTUAL\_AMOUNT} - \text{SANCTION\_AMOUNT}}{\text{SANCTION\_AMOUNT}}
   \]

#### Robust Non-Parametric Peer Z-Score & Explicit Zero-MAD Fallback Hierarchy
Rather than using arbitrary universal percentage thresholds, drift is evaluated relative to the peer category distribution. Because administrative procurement data often contains identical standard costs where \(\text{MAD} = 0\), the engine enforces an explicit **3-Tier Statistical Fallback Hierarchy**:

\[
\text{Tier 1: If } \text{MAD}_{\text{peer}} > 0 \implies M_i = 0.6745 \times \frac{\Delta_i - \text{Median}_{\text{Peer Drift}}}{\text{MAD}_{\text{peer}}}
\]
\[
\text{Tier 2: Else if } \text{IQR}_{\text{peer}} > 0 \implies Z_i = \frac{\Delta_i - \text{Median}_{\text{Peer Drift}}}{0.7413 \times \text{IQR}_{\text{peer}}}
\]
\[
\text{Tier 3: Else } (\text{MAD} = 0 \text{ and } \text{IQR} = 0) \implies \text{Deterministic Deviation Rule: } D_i = |\Delta_i - \text{Median}_{\text{Peer Drift}}|
\]
- **Operational Rule for Tier 3:**
  - If \(D_i == 0\), the work is perfectly conforming with its peer group (\(M_i = 0.0\), `severity = NORMAL`).
  - If \(D_i > 0\), the work deviates from a zero-dispersion homogeneous peer group; it is evaluated directly against configured absolute percentage drift cutoffs (\(> 10\% \implies \text{LOW}\), \(> 25\% \implies \text{MEDIUM}\), \(> 50\% \implies \text{HIGH}\)), with the metadata flag `FLAG_ZERO_DISPERSION_PEER_GROUP = TRUE`.

#### Asymmetric Severity & Epistemic Directionality
Cost overruns and cost underruns represent different operational realities. The engine distinguishes directionality without hypothesizing root causes:
- **Positive Cost Drift (\(\Delta > \text{Median}\)):** Evaluated as potential **Cost Escalation**. Receives higher anomaly severity (`ANOMALY`).
- **Negative Cost Drift (\(\Delta < \text{Median}\)):** Evaluated neutrally as **Negative Cost Drift**. The cause (savings, descoping, or partial execution) is unobserved; receives capped severity (`INFORMATIONAL` or limited `LOW` review flag).

| Severity Level | Direction & Statistical Threshold | Finding Type | Operational Classification |
| :--- | :--- | :--- | :--- |
| **NORMAL** | \(|M_i| \le 2.0\) | `INFORMATIONAL` | Within normal peer dispersion. |
| **LOW** | \(+2.0 < M_i \le +3.0\) | `ANOMALY` | Moderate positive cost escalation. |
| **MEDIUM** | \(+3.0 < M_i \le +5.0\) | `ANOMALY` | Significant positive cost escalation. |
| **HIGH** | \(M_i > +5.0\) | `ANOMALY` | Extreme positive cost escalation (> 5 MAD from peer median). |
| **INFORMATIONAL** | \(M_i < -2.0\) | `INFORMATIONAL` | Substantial negative cost drift (lower cost than peer median). |

#### Special Edge-Case Handling: Zero-Cost Completions
Across 45,704 completed works, exactly **97 records exhibit `ACTUAL_AMOUNT == 0.00`**.
- **Engine Rule:** Do **not** return `NULL` and do **not** discard.
- **Evaluation:** Evaluates mathematically to:
  \[
  \Delta_{\text{act\_sanc}} = \frac{0.00 - \text{SANCTION\_AMOUNT}}{\text{SANCTION\_AMOUNT}} = -1.00 \; (-100\%)
  \]
- **Treatment:** The work receives `sub_detector_id = "SANC_ACTUAL"`, `finding_type = DATA_QUALITY`, `severity = NORMAL`, and `data_quality_flags = ["FLAG_ZERO_COST_COMPLETION"]`. Flagged for administrative verification (e.g. project cancellation, convergence funding, clerical zero-entry) without skewing positive cost escalation models.

---

### 5.2 Secondary Supported Financial Signals

#### Signal FS1 — Low Disbursement Profiler
- **Formula:**
  \[
  \text{UTILIZATION\_RATIO} = \frac{\text{TOTAL\_DISBURSED\_AMT}}{\text{SANCTION\_AMOUNT}}
  \]
- **Eligibility:** Incomplete works with \(\ge 1\) successful payment voucher and `SANCTION_AMOUNT > 0`.
- **Configurable Prototype Defaults:** Identifies projects where `SANCTION_AGE > 180 days` AND `UTILIZATION_RATIO < 0.20`.
- **Epistemic Interpretation:** Expressed strictly as *"low observed disbursement relative to approved sanction beyond initial mobilization window"*, avoiding subjective labels such as "paralysis".

#### Signal FS2 — Cumulative Expenditure Ceiling Breach Detector
- **Formula:**
  \[
  \text{OVERRUN\_AMOUNT} = \text{TOTAL\_DISBURSED\_AMT} - \text{SANCTION\_AMOUNT} > 0
  \]
- **Regulatory Basis:** Para 4.1, MPLADS Guidelines (treasury releases must not exceed approved sanction).
- **Empirical Occurrence:** Exactly **1 record** observed in snapshot (disbursements exceeded sanction by ₹5,000).
- **Epistemic Note:** Evaluated purely as an observed financial ceiling inconsistency/breach. The engine makes no assertions regarding the internal validation mechanisms of external portals.
- **Severity:** Always **HIGH** (`finding_type = ANOMALY`).

#### Signal FS3 — Unusual Payment Voucher Amounts & Penny-Drop Checker
- **Formula:** Evaluates individual voucher amounts `FUND_DISBURSED_AMT_j` against category transaction distributions.
- **Special Sentinel:** Exactly **1 voucher** exhibits `FUND_DISBURSED_AMT == ₹0.01` (automated bank validation check).
- **Event Identity:** Uses `target_event_key = "VOUCHER_" + SNO` to guarantee unique finding identity per voucher.
- **Treatment:** Automatically tags voucher with `finding_type = DATA_QUALITY`, `severity = NORMAL`, and `data_quality_flags = ["FLAG_PENNY_DROP_PROBABLE"]`. Excluded from vendor volume rankings.

#### Signal FS4 — Payment Tranche Temporal Compression (Burst Release)
- **Mathematical Formulation:**
  For a work with \(K \ge 2\) successful payment vouchers, evaluates whether a subset of vouchers \(|S| \ge \tau_{\text{burst\_min\_vouchers}}\) (default: \(\ge 3\) vouchers) was disbursed within a compressed temporal window:
  \[
  \text{BURST\_SPAN\_DAYS} = \max_{j \in S}(\text{EXPENDITURE\_DATE}_j) - \min_{j \in S}(\text{EXPENDITURE\_DATE}_j)
  \]
- **Detection Logic:**
  Flags burst patterns where \(\text{BURST\_SPAN\_DAYS} \le 2\) calendar days (\(\le 48\) hours) for \(\ge 3\) substantial vouchers, or multiple rapid tranches compressed within 5 calendar days immediately preceding the fiscal year-end (March 26th – March 31st).

---

## 6. Core Execution & Timeline Detectors

### 6.1 Detector D2 — Completion Timeline & Duration Detector

#### Analytical Objective
Monitors certified completed works against official completion benchmarks and tracks elapsed execution age for uncompleted sanctioned works.

#### Regulatory Basis & Legitimate Exceptional Grounds
MPLADS Guidelines 2023, Para 3.2.12: *"The District Authority shall stipulate a completion period which should generally not exceed one year... in exceptional cases such as difficult/hilly terrain, more time may be allowed where justified."*
- **Epistemic Principle:** \(\text{Duration} > \text{1 Calendar Year}\) represents exceeding the standard administrative monitoring benchmark (`EXCEEDS_STANDARD_COMPLETION_WINDOW`); it is **not** automatically a procedural violation or evidence of physical stagnation.
- **Terrain & Exception Consideration:** Works located in notified hilly/difficult terrains or possessing recorded extensions are evaluated with calibrated thresholds or designated with informational exception context.

#### Calendar-Year Temporal Semantics & Epistemic Boundary
The engine strictly evaluates **recorded elapsed duration**, never physical stagnation or abandonment:
- Physical progress and civil execution are unobserved in portal records.
- Absence of a completion record indicates that no administrative completion certificate has been logged in e-SAKSHI; it does **not** prove physical halt or abandonment.
- **Monitoring Benchmark Deadline:**
  \[
  \text{COMPLETION\_DEADLINE} = \text{SANCTION\_DATE} + \text{1 Calendar Year}
  \]

```text
Sanctioned Corpus (101,511)
  ├── 1. Completed Works (45,704) ───────► COMPLETION_DURATION_DAYS = ACTUAL_END_DATE - SANC_DATE
  │
  └── 2. Uncompleted Works (55,807)
        ├── Aged > 1 Calendar Year (19,842) ──► Snapshot > COMPLETION_DEADLINE
        │
        └── Aged ≤ 1 Calendar Year (35,965) ──► NOT YET ELIGIBLE: Snapshot ≤ COMPLETION_DEADLINE
```

1. **Cohort A — Certified Completed Assets (45,704 works):**
   ```text
   COMPLETION_DURATION_DAYS = ACTUAL_END_DATE - SANCTION_DATE
   COMPLETION_OVERDUE_DAYS = max(0, ACTUAL_END_DATE - COMPLETION_DEADLINE)
   ```
2. **Cohort B — Uncompleted Sanctioned Works (55,807 works without completion certificate):**
   ```text
   ELAPSED_EXECUTION_DAYS = T_snapshot - SANCTION_DATE
   ELAPSED_OVERDUE_DAYS = max(0, T_snapshot - COMPLETION_DEADLINE)
   ```
   - **Eligible Elapsed Population:** Works where `T_snapshot > COMPLETION_DEADLINE`. Evaluated for administrative duration review (exceeding ministerial 1-year monitoring threshold without recorded completion).
   - **Ineligible Active Population:** Works where `T_snapshot <= COMPLETION_DEADLINE`. Gated as `NOT_YET_ELIGIBLE`.

#### Severity Calibration Matrix

| Severity Level | Duration / Elapsed Time | Logical Condition | Finding Type | Administrative Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **NORMAL** | ≤ 1 calendar year | `Duration <= 1 Year` | `INFORMATIONAL` | Within standard 1-year monitoring threshold. |
| **LOW** | 1 to 1.5 calendar years | `0 < Overdue_Days <= 182` | `ANOMALY` | Minor duration excess: 12 to 18 months elapsed. Review terrain context. |
| **MEDIUM** | 1.5 to 2 calendar years | `182 < Overdue_Days <= 365`| `ANOMALY` | Substantial duration excess: 18 to 24 months elapsed. |
| **HIGH** | > 2 calendar years | `Overdue_Days > 365` | `ANOMALY` | Severe duration excess: Project execution exceeds 2 full years. |

---

### 6.2 Secondary Supported Timeline Signals

#### Signal TS1 — Rapid Administrative Completion Handover
- **Formula:** `COMPLETION_DURATION_DAYS = ACTUAL_END_DATE - SANCTION_DATE`
- **Detection Logic:** Flags civil works certified complete in < 7 calendar days from sanction order.
- **Strict Epistemic Boundary:** The observable fact is solely that administrative completion certification was recorded unusually soon (< 7 calendar days) after sanction order. Detectors and explanation generators must **never** hypothesize underlying causes (e.g. claiming pre-existing assets or retroactive paper sanctions). It serves purely as an operational timeline anomaly warranting administrative verification.

#### Signal TS2 — Post-Completion Payment Lag
- **Formula:**
  ```text
  POST_COMPLETION_LAG_DAYS = max(EXPENDITURE_DATE) - ACTUAL_END_DATE
  ```
- **Detection Logic:** Flags payment vouchers disbursed > 180 days after formal project handover certification.

#### Signal TS3 — Consecutive Tranche Pacing Gap (True Pairwise Gap)
- **Mathematical Formulation:**  
  Let chronological vouchers for a work be ordered by disbursement date: \(t_1 \le t_2 \le \dots \le t_K\).  
  For works with \(K \ge 2\) vouchers, compute consecutive pairwise gaps:
  \[
  g_k = t_k - t_{k-1} \quad \text{for } k = 2, \dots, K
  \]
  \[
  \text{MAX\_TRANCHE\_GAP\_DAYS} = \max_{2 \le k \le K} (t_k - t_{k-1})
  \]
- **Eligibility:** Evaluated only when \(K \ge 2\) successful payment vouchers exist. If \(K < 2\), gated as `NOT_APPLICABLE`.
- **Detection Logic:** Flags works where the interval between consecutive disbursements exceeded a configurable threshold (e.g. \(\text{MAX\_TRANCHE\_GAP\_DAYS} > 180\) days), indicating an operational pause between civil phases.
- **Complementary Telemetry:** Days elapsed since the most recent voucher for incomplete works is tracked separately as `DAYS_SINCE_LAST_PAYMENT = T_snapshot - t_K`.

---

## 7. Common Detector Contract & Finding Schema

### 7.1 Deterministic Finding Identifier & Execution Telemetry
To guarantee 100% execution reproducibility across identical runs:
- **Finding ID Invariant:** `finding_id` is computed deterministically:
  \[
  \text{finding\_id} = \text{SHA256}(\text{detector\_id} + \text{":"} + \text{sub\_detector\_id} + \text{":"} + \text{target\_work\_key} + \text{":"} + \text{target\_event\_key} + \text{":"} + \text{config\_hash})
  \]
  *(Where `sub_detector_id` is `"NONE"` and `target_event_key` is `"NONE"` for work-level single-measurement detectors).*
  This guarantees that re-running the engine on the same snapshot with the same configuration produces identical finding IDs without collision across works or individual events.
- **Run Tracking:** A non-deterministic `execution_run_id` (UUIDv4) is tracked separately in engine operational logs to monitor batch runs and timestamps.

### 7.2 The Finding Object Specification

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DetectorFinding",
  "type": "object",
  "required": [
    "finding_id",
    "detector_id",
    "sub_detector_id",
    "target_event_key",
    "detector_category",
    "target_work_key",
    "evaluation_status",
    "severity",
    "finding_type",
    "observed_values",
    "baseline",
    "deviation",
    "threshold",
    "evidence",
    "data_quality_flags",
    "explanation"
  ],
  "properties": {
    "finding_id": { "type": "string", "description": "Deterministic SHA-256 hash" },
    "detector_id": { 
      "type": "string", 
      "enum": [
        "D1_SANCTION_DELAY", 
        "D2_COMPLETION_TIMELINE", 
        "D3_PAYMENT_INCEPTION", 
        "D3_PAYMENT_DORMANCY", 
        "D6_COST_DRIFT", 
        "D9_UNSANCTIONED_DORMANCY", 
        "FS1_UTILIZATION", 
        "FS2_OVERRUN", 
        "FS3_PENNY_DROP",
        "FS4_TRANCHE_COMPRESSION",
        "TS1_RAPID_COMPLETION", 
        "TS2_POST_COMPLETION_LAG",
        "TS3_CONSECUTIVE_TRANCHE_GAP"
      ] 
    },
    "sub_detector_id": { "type": "string", "description": "Sub-measurement identifier (e.g. REC_SANC, SANC_ACTUAL, or NONE)" },
    "target_event_key": { "type": "string", "description": "Unique event identifier for transaction-level findings, or NONE" },
    "detector_category": { "type": "string", "enum": ["COMPLIANCE", "FINANCIAL", "EXECUTION"] },
    "target_work_key": { "type": "string", "description": "Canonical 3-part work key (HOUSE_DTLID_LETTERNO)" },
    "evaluation_status": { "type": "string", "enum": ["EVALUABLE", "NOT_YET_ELIGIBLE", "INSUFFICIENT_DATA", "DATA_QUALITY_CONFLICT", "NOT_APPLICABLE"] },
    "severity": { "type": "string", "enum": ["NORMAL", "LOW", "MEDIUM", "HIGH"] },
    "finding_type": { "type": "string", "enum": ["ANOMALY", "DATA_QUALITY", "INFORMATIONAL"] },
    "observed_values": { "type": "object", "description": "Raw factual measurements extracted from source records" },
    "baseline": {
      "type": "object",
      "required": ["baseline_type", "baseline_value", "unit", "authority_reference"],
      "properties": {
        "baseline_type": { "type": "string", "enum": ["STATUTORY_MANDATE", "ADMINISTRATIVE_MONITORING", "PEER_DISTRIBUTION", "HISTORICAL_COHORT"] },
        "baseline_value": { "type": ["number", "string"] },
        "unit": { "type": "string" },
        "authority_reference": { "type": "string" }
      }
    },
    "deviation": {
      "type": "object",
      "required": ["absolute_deviation", "percentage_deviation", "z_score"],
      "properties": {
        "absolute_deviation": { "type": ["number", "null"] },
        "percentage_deviation": { "type": ["number", "null"] },
        "z_score": { "type": ["number", "null"] }
      }
    },
    "threshold": {
      "type": "object",
      "properties": {
        "low": { "type": "number" },
        "medium": { "type": "number" },
        "high": { "type": "number" }
      }
    },
    "evidence": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Factual provenance list of raw record values and timestamps"
    },
    "data_quality_flags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Applicable Phase 0 quality markers (e.g. FLAG_ORPHAN_SANCTION)"
    },
    "explanation": {
      "type": "object",
      "required": ["what_observed", "what_compared_against", "deviation_magnitude", "trigger_reason", "data_limitations"],
      "properties": {
        "what_observed": { "type": "string" },
        "what_compared_against": { "type": "string" },
        "deviation_magnitude": { "type": "string" },
        "trigger_reason": { "type": "string" },
        "data_limitations": { "type": "string" }
      }
    }
  }
}
```

---

## 8. Threshold & Configuration Model

All analytical thresholds are externalized into a single structured configuration registry with explicit temporal calculation policies:

```yaml
temporal_policy:
  d1_sanction_delay:
    mode: "fixed_days"
    value: 45
    statutory_authority: "MPLADS Guidelines 2023, Para 3.2.4"
  d3_payment_inception:
    mode: "calendar_months"
    value: 3
    monitoring_authority: "MoSPI Lok Sabha Question *44 Benchmark"
  d3_payment_dormancy:
    mode: "calendar_months"
    value: 3
    monitoring_authority: "MoSPI Lok Sabha Question *44 Benchmark"
  d2_completion_timeline:
    mode: "calendar_years"
    value: 1
    monitoring_authority: "MPLADS Guidelines 2023, Para 3.2.12"
```

| Configuration Parameter | Default Value & Unit | Regulatory / Analytical Basis |
| :--- | :--- | :--- |
| `statutory_sanction_window_days` | 45 fixed calendar days | MPLADS Guidelines 2023, Para 3.2.4 |
| `completion_monitoring_window` | 1 calendar year | MPLADS Guidelines 2023, Para 3.2.12 |
| `payment_dormancy_window` | 3 calendar months | MoSPI Starred Q#44 Monitoring Benchmark |
| `fs1_low_utilization_age_days` | 180 days | Configurable prototype analytical default |
| `fs1_low_utilization_ratio` | 0.20 (20%) | Configurable prototype analytical default |
| `ts3_consecutive_tranche_gap_days` | 180 days | Configurable prototype analytical default |
| `fs4_burst_window_days` | 2 calendar days (48 hours)| Configurable prototype analytical default |
| `fs4_burst_min_vouchers` | 3 payment vouchers | Configurable prototype analytical default |
| `peer_min_sample_size` | 30 works (\(N_{\text{min}}\)) | Initial heuristic analytical default |
| `peer_fallback_sample_size` | 10 works (\(N_{\text{perc}}\))| Initial heuristic analytical default |
| `outlier_iqr_multiplier` | 1.5 | Initial heuristic analytical default |
| `extreme_outlier_iqr_multiplier` | 3.0 | Initial heuristic analytical default |
| `robust_z_score_threshold` | 3.0 MAD | Initial heuristic analytical default |
| `premature_completion_min_days` | 7 calendar days | Physical Plausibility Threshold |
| `post_completion_payment_lag_days` | 180 calendar days | Financial Reconciliation Threshold |
| `snapshot_reference_date` | `"2026-09-21"` | Frozen Audit Snapshot Date |

---

## 9. Validation Matrix & Synthetic Fixture Specifications

To verify detector accuracy deterministically prior to downstream integration, tests evaluate against **explicit synthetic fixture datasets with predefined peer distributions**:

| Archetype ID | Test Archetype Description | Synthetic Input Fixture & Peer Context | Expected Detector | Sub Detector | Event Key | Evaluation Status | Severity | Finding Type | Rationale & Validation Invariant |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Compliant normal project | Rec: 01-Jan, Sanc: 20-Jan (19d), Paid: 10-Feb, Compl: 15-Jun | D1, D2, D3_INCEPTION, D6 | `NONE` / `REC_SANC` | `NONE` | `EVALUABLE` | `NORMAL` | `INFORMATIONAL` | Intervals within statutory limits; cost drift normal. |
| **TC-02** | Statutory sanction delay | Rec: 01-Jan, Sanc: 25-Mar (83d) | D1 | `NONE` | `NONE` | `EVALUABLE` | `MEDIUM` | `ANOMALY` | Exceeds 45-day statutory window by 38 days. |
| **TC-03** | Proposal within review window| Rec: 10-Aug, Snapshot: 21-Sep (42d) | D9 | `NONE` | `NONE` | `NOT_YET_ELIGIBLE`| `NORMAL` | `INFORMATIONAL` | Proposal age ≤ 45 days; review window open. |
| **TC-04** | Recently sanctioned unspent | Sanc: 15-Aug, Snapshot: 21-Sep (37d), Exp: 0 | D3_DORMANCY | `NONE` | `NONE` | `NOT_YET_ELIGIBLE`| `NORMAL` | `INFORMATIONAL` | Sanction age < 3 months; mobilization window open. |
| **TC-05** | Active fund dormancy | Sanc: 15-Jan, Snapshot: 21-Sep (249d), Exp: 0 | D3_DORMANCY | `NONE` | `NONE` | `EVALUABLE` | `MEDIUM` | `ANOMALY` | Incomplete unspent work older than 3 months. |
| **TC-06** | Prolonged unsanctioned proposal| Rec: 15-Jan, Snapshot: 21-Sep (249d), Sanc: None | D9 | `NONE` | `NONE` | `EVALUABLE` | `HIGH` | `ANOMALY` | Exceeds 45d review window by 204 days. Not rejected. |
| **TC-07** | Normal cost drift | Rec: ₹10.0L, Sanc: ₹10.5L (+5%)<br>*Fixture Peer: Median = +5%, MAD = 2%* | D6 | `REC_SANC` | `NONE` | `EVALUABLE` | `NORMAL` | `INFORMATIONAL` | \(M_i = 0.6745 \times \frac{0.05 - 0.05}{0.02} = 0.0 \le 2.0\). |
| **TC-08** | Positive cost escalation outlier | Sanc: ₹10.0L, Actual: ₹28.0L (+180%)<br>*Fixture Peer: Median = +10%, MAD = 5%* | D6 | `SANC_ACTUAL` | `NONE` | `EVALUABLE` | `HIGH` | `ANOMALY` | \(M_i = 0.6745 \times \frac{1.80 - 0.10}{0.05} = 22.9 > 5.0\). Escalation. |
| **TC-09** | Zero-cost completed asset | Sanc: ₹5.0L, Actual: ₹0.00 (-100%) | D6 | `SANC_ACTUAL` | `NONE` | `EVALUABLE` | `NORMAL` | `DATA_QUALITY` | Evaluates to `-1.0`; `FLAG_ZERO_COST_COMPLETION = TRUE`. |
| **TC-10** | Hard ceiling breach | Sanc: ₹5.0L, Success Payments: ₹5.05L | FS2 | `NONE` | `NONE` | `EVALUABLE` | `HIGH` | `ANOMALY` | Disbursements exceed statutory sanction by ₹5,000. |
| **TC-11** | Completed asset with zero pay| Compl: 10-Jan, Success Payments: 0 rows | D2, D3_DORMANCY | `NONE` | `NONE` | `EVALUABLE` (D2) / `NOT_APPLICABLE` (D3)| `NORMAL` | `DATA_QUALITY` | Valid completed asset; `FLAG_COMPLETED_WITHOUT_VOUCHER = TRUE`. |
| **TC-12** | Orphan sanction | Sanc: 15-Jan, Rec: None (615 orphans) | D1 | `NONE` | `NONE` | `DATA_QUALITY_CONFLICT`| `NORMAL`| `DATA_QUALITY` | Gated by `FLAG_ORPHAN_SANCTION`; excluded from rec-to-sanc. |
| **TC-13** | Sparse category peer fallback| Category N = 4 in District, N = 45 in State | D6 | `REC_SANC` | `NONE` | `EVALUABLE` | `NORMAL` | `INFORMATIONAL` | Falls back to Level 2 (`PEER_GROUP_FALLBACK = TRUE`). |
| **TC-14** | Rapid completion certification| Sanc: 10-Jan, Actual: 12-Jan (2 days) | TS1 | `NONE` | `NONE` | `EVALUABLE` | `HIGH` | `ANOMALY` | Certified complete in < 7d. Neutral explanation. |
| **TC-15** | Prolonged elapsed execution | Sanc: Jan-2024, Snapshot: Sep-2026 (>2 yrs), Compl: None| D2 | `NONE` | `NONE` | `EVALUABLE` | `HIGH` | `ANOMALY` | Elapsed execution > 2 years post-sanction. |
| **TC-16** | Penny-drop banking validation | Voucher: ₹0.01 | FS3 | `NONE` | `VOUCHER_1` | `EVALUABLE` | `NORMAL` | `DATA_QUALITY` | Tagged with `FLAG_PENNY_DROP_PROBABLE = TRUE`. |

---

## 10. Explainability Architecture (The 5 Core Questions)

Every non-normal finding emitted by Phase 1 detectors must contain a deterministic 5-part plain-language explanation generated directly from the finding attributes:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                       5 CORE EXPLAINABILITY QUESTIONS                  │
├────────────────────────────────────────────────────────────────────────┤
│ 1. What was observed?        (Factual raw values and dates)            │
│ 2. What was it compared to?  (Statutory rule or peer baseline)         │
│ 3. How large was deviation?  (Days exceeded, cost variance %, Z-score) │
│ 4. Why did it trigger?       (Exact threshold and severity rationale) │
│ 5. What limitations apply?   (Data-entry latency, missing records)     │
└────────────────────────────────────────────────────────────────────────┘
```

### 10.1 Plain-Language Generation Rules
1. **Never Assert Fraud, Guilt, or Intent:** Explanations strictly use neutral administrative terminology: *"exceeds statutory window"*, *"statistically divergent relative to peers"*, *"identified as dormant under ministerial monitoring criteria"*.
2. **Explicitly Disclose Source Limitations:** Every explanation must state relevant portal caveats (e.g. *"District data entry occurs asynchronously; observed delay reflects a combination of physical execution duration and portal entry latency"*).
3. **Traceable Numerical Provenance:** Every number cited in the text must trace directly to `observed_values`, `baseline`, or `deviation` fields in the finding contract.

---

## 11. Architectural Boundary & Governance Summary

### 11.1 Frozen Foundations (Inherited from Phase 0)
Phase 1 relies unconditionally on the following frozen guarantees from [`PHASE_0_DATA_FOUNDATION.md`](PHASE_0_DATA_FOUNDATION.md):
- **Raw Data Immutability:** 395,871 CSV rows in `data/` remain untouched.
- **Canonical Work Key:** `K_work = (HOUSE, DTL_ID, LETTER_NO)` guarantees 100.0% uniqueness across proposals.
- **Child Join Keys:** Downstream tables join on `(HOUSE, DTL_ID)` where uniqueness has been empirically verified.
- **Financial Invariants:** Prohibition against summing work ceilings across joined payment vouchers.
- **Zero Date Contradictions:** Verified 0 inverted dates within chamber partitions.
- **Explicit Payment State Filtering:** Only vouchers with `WORK_STATUS == 'Payment Success'` are aggregated into `TOTAL_DISBURSED_AMT`. `Payment In-Progress` vouchers remain in raw logs but do not count toward disbursed totals.

### 11.2 Configurable Parameters (Phase 1 Engine)
- Statutory and monitoring thresholds (45 fixed days, 1 calendar year, 3 calendar months).
- Temporal policies (`fixed_days`, `calendar_months`, `calendar_years`).
- Peer cohort dimension hierarchies by detector.
- Heuristic sample sizes and outlier multipliers (\(N_{\text{min}} = 30\), \(N_{\text{perc}} = 10\), \(1.5 \times \text{IQR}\), \(3.0 \times \text{IQR}\)).
- Zero-MAD statistical fallback rules.
- Prototype thresholds for low disbursement (FS1), burst compression (FS4), and consecutive tranche gap (TS3).

### 11.3 Explicitly Deferred Capabilities (Phase 2 & Phase 3)
The following capabilities are **strictly excluded from Phase 1** and deferred:
- **Phase 2 (Cross-Work, Entity & Pattern Intelligence):**
  - Textual recommendation similarity clustering (TF-IDF, Levenshtein, semantic embeddings).
  - Vendor market concentration (Herfindahl-Hirschman Index [HHI], agency-vendor repeat pairing rates).
  - Temporal submission bursts and fiscal-year-end proposal clustering (D8).
  - Bipartite vendor-agency relational graph network analysis.
- **Phase 3 (Risk Profiling & System Validation):**
  - Composite multi-detector risk scoring and weight calibration.
  - Interactive drill-down dashboards, REST API endpoints, and user interface components.
  - End-to-end archetype testing against CAG audit case histories.

---

## 12. Phase 1 Definition of Done Checklist

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 1 DEFINITION OF DONE CHECKLIST                            │
├──────────────────────────────────────────────────────────────────┬─────────────────────┤
│ Criterion / Requirement                                          │ Status              │
├──────────────────────────────────────────────────────────────────┼─────────────────────┤
│ 1. Three-tier baseline framework (Regulatory, Peer, Historical)  │ VERIFIED (Sec 2)    │
│ 2. Corrected statutory Guideline citations (Para 3.2.4 & 3.2.12) │ VERIFIED (Sec 2.1)  │
│ 3. RB-05 recorded as reference baseline (no Phase 1 detector)    │ VERIFIED (Sec 2.1)  │
│ 4. Detector-specific peer dimensions formalized                  │ VERIFIED (Sec 2.2)  │
│ 5. Statistical thresholds explicitly designated as heuristics    │ VERIFIED (Sec 2.2)  │
│ 6. 3-axis contract architecture (Status, Finding Type, Severity) │ VERIFIED (Sec 3.1)  │
│ 7. Explicit WORK_STATUS == 'Payment Success' filter established  │ VERIFIED (Sec 3.2)  │
│ 8. D1 Sanction Delay formalized with 45-day statutory baseline   │ VERIFIED (Sec 4.1)  │
│ 9. D3 separates Inception Delay vs Active Dormancy detectors     │ VERIFIED (Sec 4.2)  │
│ 10. D3 handles Completed without vouchers (NOT_APPLICABLE)       │ VERIFIED (Sec 4.2)  │
│ 11. D9 Unsanctioned Dormancy classified without rejection bias   │ VERIFIED (Sec 4.3)  │
│ 12. D6 sub_detector_id (REC_SANC vs SANC_ACTUAL) prevents clashes│ VERIFIED (Sec 5.1)  │
│ 13. D6 Zero-MAD 3-tier fallback hierarchy formally specified     │ VERIFIED (Sec 5.1)  │
│ 14. D6 asymmetric drift interpretation (Escalation vs Negative)  │ VERIFIED (Sec 5.1)  │
│ 15. FS1 Low Utilization defined neutrally with prototype default │ VERIFIED (Sec 5.2)  │
│ 16. FS2 ceiling breach defined neutrally without portal claims   │ VERIFIED (Sec 5.2)  │
│ 17. FS4 defined with dimensionally correct temporal burst window │ VERIFIED (Sec 5.2)  │
│ 18. D2 accounts for legitimate >1-yr exceptions & terrain        │ VERIFIED (Sec 6.1)  │
│ 19. TS1 Rapid Completion framed neutrally without causal claims  │ VERIFIED (Sec 6.2)  │
│ 20. TS3 reformulated as true pairwise consecutive tranche gap    │ VERIFIED (Sec 6.2)  │
│ 21. Deterministic finding_id SHA-256 includes target_event_key   │ VERIFIED (Sec 7.1)  │
│ 22. Externalized configuration registry defines temporal policies│ VERIFIED (Sec 8)    │
│ 23. Validation matrix defines synthetic peer distributions       │ VERIFIED (Sec 9)    │
│ 24. 5 core explainability questions formalized                   │ VERIFIED (Sec 10)   │
│ 25. Frozen, Configurable, and Deferred boundaries established    │ VERIFIED (Sec 11)   │
│ 26. Zero implementation code executed (Specification Only)       │ VERIFIED            │
└──────────────────────────────────────────────────────────────────┴─────────────────────┘
```

**Phase 1 specification is complete, mathematically sound, epistemically neutral, and authoritative. No analytical ambiguity remains that would impede implementation.**
