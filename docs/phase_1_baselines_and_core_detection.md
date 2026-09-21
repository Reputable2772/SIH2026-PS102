# Phase 1 — Baselines & Core Detection Engine

**Status:** Complete & Verified  
**Acceptance Criteria Met:** AC-03, AC-04, AC-05, AC-19  
**Source Baseline:** [Core.md](Core.md) (v0.6)

---

## 1. Executive Summary

Phase 1 establishes the deterministic policy rules, dynamic statistical peer groups, and core anomaly detectors for the analytical core. Every detector produces an explainable, auditable **Finding** object that carries raw empirical evidence, baseline comparison, mathematical severity, confidence weighting, and a concrete **Next Review Action** (mandated by AC-19).

---

## 2. Statutory & Statistical Baseline Architecture

The baseline engine calculates comparator baselines across three tiers:

### 2.1 Statutory Policy Baselines
Derived directly from the official **MPLADS Guidelines 2023** and Parliamentary monitoring frameworks:
- **Sanction SLA (Para 3.2.4):** Implementing District Authority (IDA) must sanction or reject proposals within **45 days**.
- **Execution Completion SLA (Para 3.2.12):** Maximum execution timeframe generally not exceeding **1 year (365 days)**.
- **Rajya Sabha Tenure Exception:** Post-tenure completion window extended to **540 days** (18 months).
- **Disbursement Dormancy Limit:** Ministry of Statistics monitoring parameter flagging zero disbursements after **90 days** post-sanction.

### 2.2 Hierarchical Peer Groups & Robust Scale
To avoid distorted comparisons against national averages, works are compared against granular cohorts:
$$\text{Cohort Key} = (\text{STATE\_NAME}, \text{WORK\_CATEGORY})$$
- **Minimum Sample Requirement:** $N \ge 10$ observations required for peer cohort validation.
- **Fallback Hierarchy:** If cohort $N < 10$, the engine falls back to $(\text{WORK\_CATEGORY})$ national baseline, and finally $(\text{GLOBAL})$.
- **Robust Scale ($Z$-Score):** Uses median and Normal-equivalent Interquartile Range to prevent extreme outliers from skewing the scale:
  $$\text{IQR}_{\text{norm}} = \frac{Q_{75} - Q_{25}}{1.349}, \quad Z = \frac{x - \text{Median}}{\text{IQR}_{\text{norm}}}$$

---

## 3. Core Detector Catalog

### 3.1 Compliance Detectors
- **D1 (`COMP-D1`): Sanction Turnaround SLA Breach**
  - *Trigger:* $\text{days\_rec\_to\_sanction} > 45$ days.
  - *Severity:* Scales linearly from $0.1$ at 46 days to $1.0$ at 225+ days.
  - *Next Action:* "Issue compliance inquiry to IDA to record administrative reasons for delayed approval and confirm whether Model Code of Conduct exemption applied."
- **D2 (`COMP-D2`): Execution Deadline SLA Breach**
  - *Trigger:* Elapsed duration $> 365$ days (Lok Sabha) or $> 540$ days (Rajya Sabha).
  - *Severity:* Scales with excess delay beyond the statutory ceiling.
  - *Next Action:* "Direct Implementing Agency to submit physical inspection log, assess liquidated damages, and verify time extension approval."
- **D3 (`COMP-D3`): Stalled Initial Disbursement**
  - *Trigger:* $\text{days\_since\_sanction} > 90$ days with $\text{total\_disbursed} = 0$ on ongoing works.
  - *Severity:* Scales from $0.3$ at 91 days to $1.0$ at 270+ days.
  - *Next Action:* "Issue show-cause inquiry to District Authority to determine whether tender was awarded, site was encumbered, or funds should be surrendered."
- **D4 (`COMP-D4`): Irregular Lifecycle Sequence**
  - *Trigger:* Retroactive sanctions ($\text{days} < 0$), completion before sanction, or vouchers preceding sanction.
  - *Severity:* Fixed $0.85$ (Critical governance irregularity).
  - *Next Action:* "Demand administrative audit trail and original physical dispatch register from District Magistrate to confirm authenticity of approval dates."

### 3.2 Financial Anomaly Detectors
- **D5 (`FIN-D5`): Peer Group Cost Outlier**
  - *Trigger:* Robust $Z \ge 2.5$ relative to $(\text{STATE\_NAME}, \text{WORK\_CATEGORY})$ peer median.
  - *Confidence:* Calibrated by $\min(1.0, \log_{10}(N)/3.0)$ and record DQI.
  - *Next Action:* "Request verified Schedule of Rates (SOR) analysis and technical estimate justification from District Planning Authority."
- **D6 (`FIN-D6`): Sanction Cost Overrun**
  - *Trigger:* Total disbursed $> 105\%$ of approved administrative sanction amount.
  - *Severity:* Proportional to unauthorized percentage overrun.
  - *Next Action:* "Demand revised sanction order signed by District Magistrate; if missing, withhold further releases and initiate recovery of excess disbursements."
- **D8 (`FIN-D8`): Temporal Disbursement Spike**
  - *Trigger:* $\ge 3$ payment vouchers totaling $\ge ₹10,00,000$ disbursed in $\le 7$ days.
  - *Next Action:* "Verify physical stage-gate inspection certificates for each voucher tranche to confirm genuine milestone attainment prior to rapid successive releases."

### 3.3 Execution & Agency Detectors
- **D9 (`EXEC-D9`): Progress-Expenditure Mismatch**
  - *Trigger:* Work has drawn $\ge 85\%$ of budget and exceeded 365 days, yet lacks completion certification.
  - *Next Action:* "Dispatch District Quality Monitor (DQM) for geo-tagged visual site inspection and impound contractor final bill pending handover certificate."
- **D11 (`AGY-D11`): Implementing Agency Capacity Overload**
  - *Trigger:* IA burdened with $\ge 10$ delayed unfinished works exceeding 1 year and $\ge ₹50,00,000$ committed funds.
  - *Next Action:* "Enforce administrative moratorium on assigning new works to this agency and review re-allocation to alternative engineering divisions."

---

## 4. Implementation Verification

- **Code:** [src/engine/baselines.py](../src/engine/baselines.py), [src/engine/detectors/base.py](../src/engine/detectors/base.py), [src/engine/detectors/compliance.py](../src/engine/detectors/compliance.py), [src/engine/detectors/financial.py](../src/engine/detectors/financial.py), [src/engine/detectors/execution.py](../src/engine/detectors/execution.py), [src/engine/detectors/agency.py](../src/engine/detectors/agency.py), [src/engine/detectors/__init__.py](../src/engine/detectors/__init__.py).
- **Unit Tests:** [tests/test_phase_1.py](../tests/test_phase_1.py) verifying baseline math, all 9 detectors, and Next Review Action completeness (All passing).
