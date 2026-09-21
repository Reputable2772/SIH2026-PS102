# Phase 0 — Data Foundation & Analytical Model

**Status:** Complete & Verified  
**Acceptance Criteria Met:** AC-01, AC-02, AC-14  
**Source Baseline:** [Core.md](Core.md) (v0.6)

---

## 1. Executive Summary

Phase 0 establishes the empirical bedrock of the MPLADS Intelligence Engine. It processes **421,500+ raw transactional records** across 15 official e-SAKSHI CSV datasets covering all 36 States/UTs, 543 Lok Sabha constituencies, and 245 Rajya Sabha seats. 

The pipeline normalizes disparate date encodings, sanitizes financial values, repairs corrupted identifiers, and reconstructs the canonical **Work** entity across its full administrative lifecycle.

---

## 2. Dataset Inventory & Relational Architecture

The analytical core ingests two parallel sets of granular tables representing the bicameral structure of the Parliament of India, anchored by administrative masters:

| Dataset | Granularity | Scope (Lok Sabha / Rajya Sabha) | Key Relational Identifiers |
|---|---|---|---|
| **Recommended Works** | Project proposal | 117,459 / 28,540 rows | `WORK_RECOMMENDATION_DTL_ID`, `CONSTITUENCY_ID` |
| **Sanctioned Works** | Administrative approval | 88,386 / 22,584 rows | `WORK_RECOMMENDATION_DTL_ID`, `WORK_ID`, `LETTER_NO` |
| **Vendor Expenditures** | Payment voucher line-item | 86,339 / 25,598 rows | `WORK_RECOMMENDATION_DTL_ID`, `VENDOR_ID`, `IA_NAME` |
| **Completed Works** | Physical asset sign-off | 39,142 / 11,808 rows | `WORK_RECOMMENDATION_DTL_ID`, `WORK_ID`, `ACTUAL_END_DATE` |
| **MP Allocations** | Entitlement balances | 544 / 233 rows | `MP_NAME`, `CONSTITUENCY`, `TENURE` |
| **Calamity Consents** | Quota surrender | 13 / 21 rows | `MP_NAME`, `CALAMITY_NAME`, `CONSENTED_AMOUNT` |
| **Administrative Masters**| Reference tables | 37 States, 797 Districts, 5 Tenures | `STATE_ID`, `DISTRICT_ID`, `TENURE_ID` |

### Empirical Join Fidelity
A rigorous key audit on primary and foreign keys confirmed high relational coherence:
- **Sanctioned $\to$ Recommended Linkage:** $99.5\%$ match rate on `WORK_RECOMMENDATION_DTL_ID`.
- **Expenditures $\to$ Sanctioned Linkage:** $100.0\%$ match rate ($57,845$ unique works linked to vouchers).
- **Completed $\to$ Sanctioned Linkage:** $100.0\%$ match rate ($35,561$ unique works linked to completion assets).
- **Vendor Identity Verification:** Both `VENDOR_NAME` and `IA_NAME` are **$100.0\%$ populated** across all 111,937 expenditure records, empirically validating contractor-level and agency-level analytics for subsequent phases.

---

## 3. Canonical Work Entity & Lifecycle Model

The canonical `Work` representation unifies fragmented multi-stage records into a single analytical unit:

```text
RECOMMENDATION ────────► SANCTION ────────► EXECUTION / DISBURSEMENT ────────► COMPLETION
 (MP Proposal)         (IDA Approval)             (IA & Vendor Vouchers)          (Physical Handover)
       │                      │                              │                            │
  RECOMMENDED_AMT        SANCTION_AMT                FUND_DISBURSED_AMT               ACTUAL_AMOUNT
  RECOMMENDATION_DATE    SANCTION_DATE               EXPENDITURE_DATE                 ACTUAL_END_DATE
```

### Computed Operational Durations
1. **`days_rec_to_sanction`**: $\text{SANCTION\_DATE} - \text{RECOMMENDATION\_DATE}$
   - Governed by Statutory 45-day SLA (Para 3.2.4).
2. **`days_sanction_to_first_payment`**: $\min(\text{EXPENDITURE\_DATE}) - \text{SANCTION\_DATE}$
   - Tracks ministerial stall parameter (breach if $>90$ days).
3. **`days_sanction_to_completion`**: $\text{ACTUAL\_END\_DATE} - \text{SANCTION\_DATE}$
   - Governed by Statutory 1-year general execution deadline (Para 3.2.12).
4. **`days_since_sanction`**: $\text{SNAPSHOT\_DATE} - \text{SANCTION\_DATE}$
   - Real-time age tracking for ongoing incomplete works.

---

## 4. Multidimensional Data Quality Index (DQI)

Every work is tagged with a composite Data Quality Index ($DQI \in [0.0, 1.0]$) composed of 4 orthogonal dimensions:
$$\text{DQI} = 0.25 \cdot S_{\text{id}} + 0.25 \cdot S_{\text{date}} + 0.25 \cdot S_{\text{fin}} + 0.25 \cdot S_{\text{desc}}$$

1. **Identifier Completeness ($S_{\text{id}}$):** Valid presence of `WORK_RECOMMENDATION_DTL_ID` ($0.50$), `STATE_NAME` ($0.25$), and `IDA_NAME` ($0.25$).
2. **Date Integrity ($S_{\text{date}}$):** Non-null `SANCTION_DATE` ($0.50$) and non-negative recommendation-to-sanction duration ($0.50$).
3. **Financial Validity ($S_{\text{fin}}$):** Non-zero `SANCTION_AMOUNT` ($0.60$) and valid non-negative disbursement total ($0.40$).
4. **Descriptive Richness ($S_{\text{desc}}$):** Length of `WORK_DESCRIPTION` normalized against 50 characters: $\min(1.0, \frac{\text{len}}{50})$.

---

## 5. Explicit Data-Quirk & Anomaly Handling

Phase 0 surfaces data quality deviations rather than silently discarding them:
- **Retroactive Sanctions:** Flagged when `days_rec_to_sanction < 0` (sanction recorded before recommendation date).
- **Premature Completion:** Flagged when `days_sanction_to_completion < 0`.
- **Pre-Sanction Disbursement:** Flagged when payments occur prior to formal sanction date.
- **Negative / Zero Values:** Financial values are clamped to non-negative floats with explicit zero-amount anomaly tags.

---

## 6. Implementation Verification

- **Code:** [src/data/loader.py](../src/data/loader.py), [src/data/normalizer.py](../src/data/normalizer.py), [src/data/lifecycle.py](../src/data/lifecycle.py), [src/data/quality.py](../src/data/quality.py), [src/data/pipeline.py](../src/data/pipeline.py).
- **Unit Tests:** [tests/test_phase_0.py](../tests/test_phase_0.py) covering normalizer parsing, lifecycle state transitions, DQI scoring, and coverage calculations.
