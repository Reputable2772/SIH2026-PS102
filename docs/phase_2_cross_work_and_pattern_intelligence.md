# Phase 2 — Cross-Work, Entity & Pattern Intelligence

**Status:** Complete & Verified  
**Acceptance Criteria Met:** AC-06, AC-07, AC-08  
**Source Baseline:** [Core.md](Core.md) (v0.6)

---

## 1. Executive Summary

Phase 2 elevates the analytical core from isolated, single-work inspection to **relational and cross-record pattern intelligence**. It discovers candidate duplicate works across municipal boundaries, detects district-level monopolization by Implementing Agencies and commercial contractors, traces systemic entity recurrence across independent anomalies, and evaluates macro-level aggregate trends over time.

> [!IMPORTANT]
> **Deterministic Phase 2 Invariant:** Consistent with the architectural design principles of `Core.md`, Phase 2 executes **strictly rule-based and statistical algorithms**. Machine learning models (unsupervised anomaly ensembles and supervised breach predictors) are strictly deferred to Phase 4.

---

## 2. Similarity & Duplicate Work Detection Engine (`SIM-D12`)

The duplicate detection engine identifies potential double-billing, copied proposals, or scope overlap without requiring manual cross-checking of thousands of works:

### 2.1 Candidate Blocking & Filtering
To prevent computationally intractable quadratic comparisons ($O(N^2)$ across $101,500+$ works), candidate pairs are blocked by:
1. **Geographic & Category Block:** Comparing works within the same `(STATE_NAME, WORK_CATEGORY)` cohort.
2. **Financial Proximity Window:** Restricting comparison to works whose approved budgets are within $\pm 20\%$ of each other:
   $$\frac{|C_1 - C_2|}{\max(C_1, C_2)} \le 0.20$$

### 2.2 Textual Feature Extraction & Scoring
- **TF-IDF Character & Word N-Grams:** Extracts n-grams ($1 \le n \le 3$) across normalized `WORK_DESCRIPTION` strings.
- **Cosine Similarity Threshold:** Flags work pairs where text cosine similarity $\text{Sim} \ge 0.82$.
- **Spatial Proximity Weighting:** If the pair also belongs to the same `IDA_NAME` (same district authority), a $10\%$ confidence and severity boost is applied.
- **Output:** Flagged as an administrative **Review Candidate**, not a binary fraud verdict.

---

## 3. Entity Concentration & Monopolization Analysis

### 3.1 Implementing Agency Monopolization (`AGY-D13`)
Measures the concentration of public works assigned to executing agencies within each district using the **Herfindahl-Hirschman Index (HHI)**:
$$\text{HHI} = \sum_{i=1}^{k} s_i^2$$
where $s_i$ is the percentage share ($0 \le s_i \le 100$) of total district works managed by agency $i$.
- **Trigger:** District $\text{HHI} \ge 2,500$ (DOJ/FTC standard for highly concentrated markets) AND single agency share $\ge 40\%$ across $\ge 15$ district works.
- **Next Review Action:** Mandate open distribution of future project sanctions across alternative state engineering departments to eliminate single-agency bottlenecks.

### 3.2 Vendor Payment Monopolization (`VND-D14`)
Leverages the $100\%$ populated `VENDOR_NAME` field in the e-SAKSHI expenditure dataset:
- **Trigger:** A commercial contractor captures $\ge 50\%$ of all disbursed vendor funds in a district across $\ge 5$ distinct works.
- **Next Review Action:** Examine e-procurement tender logs for bid rigging, single-bidder awards, or non-competitive tender splitting.

---

## 4. Systemic Entity Recurrence (`REC-D15`)

Phase 2 correlates findings generated across Phase 1 detectors (turnaround delays, cost overruns, stalled disbursements, and execution mismatches) against the associated `ia_name` and `primary_vendor`:
- **Trigger:** When a single agency or contractor is tied to $\ge 3$ distinct anomalous works.
- **Significance:** Separates random, isolated project delays from institutional execution pathologies or habitual contractor underperformance.

---

## 5. Macroeconomic & Longitudinal Trend Analysis

The `TrendAnalyzer` computes annual velocity, cost growth, and completion dynamics across financial years:
1. **Sanction Turnaround Velocity:** Tracks year-over-year changes in average days required for sanction approvals.
2. **Category Cost Trajectories:** Monitors median cost escalation across priority sectors (e.g. Drinking Water, Community Halls, Education).
3. **Completion Velocity:** Computes real-time completion rates per sanction cohort to track backlog accumulation.

---

## 6. Implementation Verification

- **Code:** [src/engine/cross_work/similarity.py](../src/engine/cross_work/similarity.py), [src/engine/cross_work/concentration.py](../src/engine/cross_work/concentration.py), [src/engine/cross_work/recurrence.py](../src/engine/cross_work/recurrence.py), [src/engine/cross_work/trends.py](../src/engine/cross_work/trends.py), [src/engine/cross_work/__init__.py](../src/engine/cross_work/__init__.py).
- **Unit Tests:** [tests/test_phase_2.py](../tests/test_phase_2.py) verifying similarity thresholds, HHI math, vendor capture, recurrence tracking, and trend series (All passing).
