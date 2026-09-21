# MPLADS Intelligence Engine

## Core Prototype — Project Specification & Implementation Guide

**Problem:** SIH26102 / PS102  
**Scope:** Analytical core only  
**Status:** Implementation baseline (v0.6 — phase-tagged acceptance criteria, split definitions of done, explicit Phase 4 implementation requirement, explicit breach-label observation/stall rule, deterministic Phase 2 boundaries, and sanction-time feature eligibility)

---

## Requirements / Constraints

### Objective

Build an independent analytical engine that consumes available MPLADS/eSAKSHI records and produces **ranked, explainable anomalies and review priorities**.

The core shall address:

- expenditure and utilization anomalies;
- cost anomalies / overruns;
- execution and timeline anomalies;
- potentially duplicate or highly similar works;
- unusual vendor / Implementing Agency patterns;
- aggregate trends;
- combinations of multiple weak signals.

This corresponds to the SIH requirement for identifying trends, anomalies, irregularities, potential fraud, cost overruns, duplicate works, delayed projects, deviations from norms and risk-based alerts across MPLADS data.

### Constraints

- Independent of frontend/backend.
- No detector may silently depend on unavailable data.
- Missing/incomplete data must be explicit.
- Anomalies must not be presented as confirmed fraud or wrongdoing.
- Every high-priority finding must have evidence and explanation.
- Regulatory deviations and statistical anomalies must remain distinct.
- Detectors must be modular and independently testable.
- Thresholds, peer definitions and risk weights must be configurable.
- Historical comparisons must account for data-coverage differences.

eSAKSHI provides integrated recommendation, sanction, execution/progress and payment workflows from April 2023 onward, while MoSPI documents limitations in earlier online coverage. ([pib.gov.in](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2235932&lang=2&reg=3))

---

## Implementation Guidelines

### Preferred approach

Use a **hybrid, explainable anomaly-detection architecture**:

**deterministic rules → statistical analysis → cross-record analysis → multivariate anomaly detection → composite risk assessment**

### Detection philosophy

- **Rules:** explicit MPLADS/process deviations.
- **Statistics:** unusual behaviour relative to peer or historical baselines.
- **Similarity:** potentially duplicated/highly similar works.
- **Relationships:** unusual vendor/agency/entity patterns.
- **Trends:** meaningful aggregate changes over time.
- **ML:** unusual combinations of otherwise interpretable characteristics.

**Rules-first, ML-second is a deliberate phasing decision, not a capability or data limitation.** Deterministic rules and statistical baselines are built first because they are auditable and independently verifiable — they give the system a trustworthy, explainable foundation before any model output enters the picture. Multivariate ML-based anomaly detection is layered on top only once that foundation is validated, specifically to surface irregularities the explicit rules and baselines cannot articulate. ML augments and is checked against the rule/statistics layer — it never operates as the sole basis for a finding, and it is not deferred because it cannot be built; it is deferred because it should not be trusted first.

### Design rules

- Prefer simple, explainable methods.
- Compare against appropriate peers, not global averages.
- Preserve evidence behind every finding.
- Make policy values configurable.
- Separate observed facts, comparisons and inferred anomalies.
- Design around actually available data.
- Start with structured data.
- Optimize for **review prioritization**, not binary fraud classification.

MPLADS guidelines include explicit operational constraints such as sanction/rejection timelines and generally no more than one year for completion; these should be represented as configurable policy rules. ([mplads.gov.in](https://www.mplads.gov.in/MPLADS/En/2034.aspx))

---

## Architecture

```text
                 MPLADS / eSAKSHI DATA
                          │
                          ▼
                  Data Foundation
                 / Normalization
                          │
                          ▼
                 Work Reconstruction
                   + Lifecycle
                          │
                          ▼
                  Baseline Engine
              Policy / Peer / Historical
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
  Compliance          Financial          Execution
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
        Similarity                 Relationships
             └────────────┬────────────┘
                          ▼
                    Trend Analysis
                          │
                          ▼
               Multivariate Anomaly
                          │
                          ▼
                    Risk Assessment
                          │
                          ▼
                 Evidence / Reasons
                          │
                          ▼
                 Ranked Findings
```

### Primary entity

**Work** is the primary unit of analysis.

Where available, it contains:

- identity, description and category;
- location and administrative context;
- MP / constituency;
- recommendation;
- sanction;
- cost;
- expenditure;
- payments;
- progress;
- completion;
- Implementing Agency;
- vendor/payee;
- supporting evidence.

Secondary entities include:

**MP → Work → Implementing Agency → Vendor → Payment**

### Lifecycle

**Recommendation → Sanction → Execution → Progress → Payments → Completion**

This reflects the current eSAKSHI workflow. ([pib.gov.in](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2235932&lang=2&reg=3))

---

## Functional Requirements

### FR-01 — Data Foundation

Normalize source datasets; handle inconsistent fields, dates, financial values, identifiers, missing data, duplicate/aggregate rows and other data-quality issues.

### FR-02 — Work Reconstruction

Associate records referring to the same work and reconstruct its available lifecycle.

### FR-03 — Baselines

Provide:

- **regulatory** baselines from MPLADS rules;
- **peer** baselines for comparable works;
- **historical/behavioural** baselines where coverage permits.

### FR-04 — Compliance Detection

Detect configurable deviations such as delayed sanction/rejection, prolonged completion, financial inconsistencies, missing lifecycle transitions and other identifiable procedural deviations.

### FR-05 — Financial Anomaly Detection

Detect:

- unusual project costs;
- peer-group cost outliers;
- abnormal utilization;
- expenditure inconsistent with sanction;
- unusual payment patterns;
- unusual temporal concentration of payments.

Where vendor identity or payment-stage identity is unavailable, detectors must downgrade to the strongest supported aggregate/payment-level analysis rather than inventing vendor-level or stage-level observations.

### FR-06 — Execution Anomaly Detection

Detect:

- delayed works;
- stalled works;
- unusually long execution;
- progress/expenditure mismatch;
- inconsistent lifecycle states.

### FR-07 — Similarity / Duplicate Detection

Identify candidate duplicate or highly similar works using combinations of description, location, category, cost, time and administrative context.

Output is a **review candidate**, not a declaration of duplication or fraud.

### FR-08 — Relationship Analysis

Identify unusual:

- **Agency concentration** — buildable now. `implementing_agency_name` is present in the current public MPLADS datasets, so IA-level concentration and relationship analysis are in scope for Phase 2. Initial supported analyses include:
  - share of a district's work volume and/or expenditure attributable to an IA;
  - IA activity across multiple districts;
  - repeat IA–MP pairing;
  - IA concentration within an IDA.
  These are descriptive concentration/relationship measures, not findings of impropriety.

- **Vendor concentration** — **pending dataset verification; do not build against assumed identity data.** No current public MPLADS dataset is assumed to carry a vendor/contractor identity field until the public dashboard or mentor-provided sample is verified. The 6 March 2026 eSAKSHI public dashboard revamp adds drill-down "amounts released as vendor payments," but it is unconfirmed whether this exposes vendor *identity* or only aggregate payment *amounts*. These support materially different detectors.

- recurrence of entities across anomalies;
- combinations of related works/entities.

### FR-09 — Trend Analysis

Identify meaningful changes over time at relevant levels such as state, district, constituency, agency, vendor, work category and financial year, subject to availability and coverage of the relevant entity field.

### FR-10 — Multivariate Anomaly Detection

Identify unusual combinations of features that may not trigger individual detectors. This requirement is implemented only in **Phase 4**.

### FR-11 — Risk Assessment

Combine detector outputs into configurable review-priority levels:

- Normal
- Low
- Medium
- High

Risk is scored on two separate axes, not collapsed into one number:

- **Severity** — how far the finding deviates from its baseline.
- **Confidence** — how reliable that baseline is (peer-group sample size, data completeness for the relevant state/period). A severe deviation measured against a 3-work peer group is not the same finding as an identical deviation measured against a 500-work peer group; both must stay visible.

Component signals must remain visible.

### FR-12 — Explainability

Every significant finding must state:

- what was detected;
- observed values;
- comparison/baseline;
- deviation/similarity strength;
- related records/entities;
- relevant limitations;
- a suggested next review action (e.g. request Utilisation Certificate, verify completion photo, cross-check with District Authority) — the finding should point toward what a reviewer does next, not stop at what was observed.

### FR-13 — Ranked Output

Produce a ranked set of works/entities for human review.

### FR-14 — Data Reliability

Distinguish:

**potential anomaly in the work**

from

**anomaly caused by incomplete/inconsistent data**.

---

## Non-Functional Requirements

### Explainability

No high-priority finding without an understandable analytical basis.

### Reproducibility

Same data + same configuration → reproducible results.

### Modularity

Detectors must be independently executable, tested and replaceable.

### Auditability

Each finding must be traceable to source observations and analytical comparisons.

### Configurability

Policy thresholds, peer definitions, anomaly thresholds, detector weights and risk boundaries must be configurable.

### Reliability

Missing/malformed fields must affect only the relevant analysis, not corrupt the overall assessment.

### Performance

The prototype must process its demonstration dataset without impractical delays. Production-scale throughput is out of scope.

### Security / Data Handling

- use only required information;
- preserve source provenance;
- do not modify source records;
- keep outputs traceable;
- do not infer unsupported intent or personal attributes.

---

## Implementation Plan

### Phase 0 — Data Foundation & Analytical Model

**Goal:** Establish what can actually be built and create the unified analytical foundation.

- Obtain and audit representative MPLADS/eSAKSHI datasets.
- Inventory fields, identifiers, coverage and relationships.
- Identify missing/incomplete information and feasible detectors.
- Normalize records, including dates, financial values, identifiers, duplicates and aggregates.
- Define the canonical **Work** representation.
- Reconstruct the available work lifecycle.
- Establish MP, work, Implementing Agency, vendor and payment relationships where those entities are actually available.
- Implement explicit data-quality and missing-data handling.

**Deliverable:** Unified analytical dataset + Data Map + Coverage Matrix.

---

### Phase 1 — Baselines & Core Detection

**Goal:** Establish comparison baselines and implement the primary anomaly detectors.

- Encode relevant MPLADS/process rules as configurable policy baselines.
- Establish appropriate peer groups.
- Calculate historical/behavioural baselines where coverage permits.
- Define minimum sample requirements.
- Implement:
  1. Compliance detection
  2. Financial anomaly detection
  3. Execution/timeline anomaly detection
- Implement any Phase 1 agency-level analysis supported by verified `implementing_agency_name` availability.
- Each detector produces: **Finding + Severity + Confidence + Evidence + Explanation + Next Review Action**.

**Deliverable:** Baseline specification + independent core detector outputs.

---

### Phase 2 — Cross-Work, Entity & Pattern Intelligence

**Goal:** Detect signals that require relationships across works, entities or time.

- Implement similarity / duplicate-work detection.
- Implement Implementing Agency relationship and concentration analysis.
- Add vendor concentration only once FR-08's dataset-verification question (identity vs. amount-only) is resolved — not before.
- Identify recurrence of entities across anomalous works.
- Implement aggregate trend analysis covering:
  - anomaly rates;
  - costs;
  - delays;
  - expenditure;
  - recurring entity patterns.

**Deliverable:** Cross-record findings + trend findings.

**Explicit boundary:** Phase 2 does **not** train or execute ML models. Multivariate anomaly detection is implemented only in Phase 4 after the rule/statistical core (Phases 0–3) is frozen and validated.

---

### Phase 3 — Risk, Explainability & Validation

**Goal:** Convert detector outputs into stable, reviewable and validated priorities.

- Establish configurable component scores, detector weights and risk levels.
- Incorporate confidence and data-quality handling.
- Combine detector outputs into unified review priorities using rule/statistical signals only.
- Ensure every significant finding answers: **What happened? Why is it unusual? Compared with what? What evidence supports it? What are the limitations? What should a reviewer do next?**
- Validate against:
  - normal works;
  - cost anomalies;
  - timeline anomalies;
  - duplicate-like works;
  - payment anomalies;
  - relationship anomalies;
  - multi-signal cases;
  - ambiguous/legitimate exceptions.
- Test controlled anomaly injection.
- Document data limitations and detector behaviour.
- **Validation benchmark:** pull named irregularities from a specific state's CAG MPLADS audit report, run the pipeline against the matching state/period, and report recall as a concrete number (e.g. "flagged N of M independently-named cases") — not a qualitative pass/fail.
- **Coverage-bias check:** test whether flag rates correlate with data-completeness/digitization coverage (by state, and by LS vs. RS) rather than with genuine irregularity. Document any correlation found — an uncontrolled version of this looks identical to a real finding and will be the first thing a knowledgeable judge asks about.
- Freeze the rule/statistical core once risk aggregation is stable, outputs are explainable, validation passes and demonstration scenarios work end-to-end. Phase 4 reopens the composite scorer only to add trained ML signals; no existing Phase 0–3 rule/statistical detector is silently changed as part of that reopening.

**Deliverable:** Validated, explainable, configurable MPLADS review-prioritization engine (rule/statistical core), plus a reported validation-recall number and a documented coverage-bias check.

### Demonstration Scope

The live walkthrough runs against a curated slice, not the full national dataset cold: 2–3 states with complete eSAKSHI-era coverage and at least one CAG-documented case each, chosen so the validation benchmark above and the live demo are the same story, not two different ones.

---

### Phase 4 — ML Training & Integration on Real Data

**Implementation requirement:** Phase 4 is an execution/implementation phase, not a specification phase. Its deliverable is trained model artifacts, evaluation results, and generated findings — not another design document. The models described below must actually be implemented, trained on real MPLADS data, evaluated, persisted, and executed to produce findings on the current dataset. Do not produce a further specification-only document for Phase 4 unless a concrete implementation blocker is discovered and documented as such.

**Goal:** Train and validate ML models on actual MPLADS data — not synthetic — and integrate their output into the composite risk score as supporting signals, consistent with the rules-first/ML-second decision.

#### Component A — Unsupervised Anomaly Ensemble

- Construct feature vectors from the validated Phase 0–3 dataset — reuse existing peer groups, baselines and category encodings; do not invent parallel feature definitions.
- Train the anomaly model (e.g. Isolation Forest / Local Outlier Factor) on the real dataset assembled in Phase 0.
- Validate output against Phase 1–3 rule-flagged cases and against any available known-case references.
- Report the proportion/overlap of model findings with existing rule/statistical findings, while also retaining novel ML-only findings for review.
- Persist the fitted model and the exact preprocessing/configuration required to reproduce its outputs.

#### Component B — Supervised Breach-Risk Model

This does not require fraud labels, which do not exist publicly. It requires outcome labels derived from observed lifecycle outcomes.

- **Outcome-label eligibility:** a work is eligible for training only when `snapshot_date - sanction_date` exceeds the mandated observation window. For the current policy configuration, use **365 days**, or **540 days for the specified RS post-tenure exception**, as applicable.
- Works that have not yet had enough observation time are **excluded from training entirely**; they are never silently labeled `0` merely because no breach has yet been observed.
- **Breach label construction:** within the eligible observation window:
  - `breached = 1` if the resolved work exceeds its applicable completion window **or** satisfies the configured stall rule;
  - `breached = 0` if the observation window is complete and the work remains within the applicable completion window without satisfying the stall rule.
- **Stall rule:** the implementation must use an explicit configurable threshold for a qualifying period with no observed progress event after sanction. A default value must be recorded in configuration and the event types counted as progress must be documented. Do not infer physical stagnation merely from the absence of a completion record.
- Train only on features demonstrably knowable at or before sanction time. Any field first observed during execution, payment or completion is excluded from the supervised feature set, even if it is present in the analytical dataset.
- Eligible examples with ambiguous/conflicting outcome evidence are excluded from supervised training or routed through explicit data-quality handling rather than forced into either class.
- Use a temporal holdout: train on earlier sanctions and test on later sanctions.
- Report AUC-ROC and precision-recall metrics as concrete numbers. Where class imbalance materially affects interpretation, also report class prevalence and a suitable precision-recall baseline.
- Apply the trained model to currently in-progress works that satisfy the model's feature-availability requirements to produce a breach-risk probability — this, not the anomaly ensemble, is the system's actual predictive-insight / early-warning capability.

#### Integration (both components)

- Normalize both models' outputs to the same [0,1] scale as the other signals where appropriate. Preserve the native model metric in the finding for auditability.
- Reopen the Phase 3 composite scorer only after the Phase 0–3 rule/statistical core is frozen and validated.
- Add both trained-model signals as additional weighted supporting signals.
- Model output must carry the same evidence/reasons as every other signal (FR-12) — it does not get to bypass explainability.
- Re-run Phase 3's validation scenarios end-to-end to confirm neither addition destabilizes the already-validated rule-based rankings.
- Record the exact model version, training snapshot, feature set, preprocessing configuration and evaluation metrics with the integrated output.

**Deliverable:** Two models — an unsupervised anomaly ensemble and a supervised breach-risk predictor — both trained and validated on real data, both integrated into the composite risk score without weakening explainability.

---

## Acceptance Criteria

The core is complete when — each criterion is tagged with the phase it belongs to; none apply before that phase is built.

### AC-01 (Phase 0)

Representative MPLADS data can be analysed end-to-end.

### AC-02 (Phase 0)

Available records can be reconstructed into work lifecycles.

### AC-03 (Phase 1)

Relevant compliance deviations can be detected.

### AC-04 (Phase 1)

Financial anomalies can be identified against appropriate baselines.

### AC-05 (Phase 1)

Execution/timeline anomalies can be detected.

### AC-06 (Phase 2)

Potentially similar/duplicate works can be surfaced.

### AC-07 (Phase 2)

Unusual agency concentration and relationship patterns can be identified where implementing-agency identity is available. Vendor concentration is excluded until FR-08's dataset-verification question is resolved.

### AC-08 (Phase 2)

Meaningful aggregate trends can be surfaced.

### AC-09 (Phase 4)

A supporting multivariate anomaly signal can be generated from a model actually trained on real MPLADS data.

### AC-10 (Phase 3, extended in Phase 4)

Detector outputs can be combined into configurable review-priority levels. Phases 0–3 combine rule/statistical signals only; Phase 4 reopens this scorer to add both trained-model signals.

### AC-11 (Phase 3 onward)

Every high-priority result contains concrete evidence and explanation.

### AC-12 (all phases)

Anomalies are never presented as confirmed fraud or intentional wrongdoing. This is a constraint on every phase's output, not a deliverable of any single one.

### AC-13 (Phase 3)

Controlled anomalies can be injected and detected.

### AC-14 (Phase 0 detection, Phase 3 reporting)

Important data limitations are surfaced rather than silently ignored.

### AC-15 (Phase 4)

The multivariate anomaly model is trained and validated on real MPLADS datasets — no synthetic data — and its output is integrated into the composite risk score without bypassing the explainability requirement (FR-12).

### AC-16 (Phase 3)

A recall benchmark against named CAG-documented irregularities is computed and reported as a concrete number, not asserted qualitatively.

### AC-17 (Phase 3)

Flag rates are tested for correlation with data-completeness/digitization coverage across states and LS/RS terms, and any correlation found is documented rather than mistaken for a genuine finding.

### AC-18 (Phase 4)

The supervised breach-risk model's AUC-ROC and precision-recall on a temporal holdout are computed and reported.

### AC-19 (Phase 1 onward)

Every finding includes a recommended next review action, not only observed evidence. This applies incrementally as each phase starts producing findings — Phase 1's rule-engine output must carry it from the start, not just the final Phase 4 output.

---

## Out of Scope / Deferred

### Core exclusions

- frontend;
- dashboards;
- backend/API;
- authentication/user management;
- production database;
- cloud deployment;
- mobile application;
- autonomous case decisions.

### Deferred analytical capabilities

- OCR;
- document understanding;
- image verification/reuse detection;
- satellite imagery;
- GPS/site verification;
- advanced graph ML;
- automated investigation workflows;
- external-data enrichment;
- richer evidence analysis.

These should be considered only after the structured-data core is validated. Predictive completion forecasting was previously listed here and has been moved to Phase 4, Component B — it is now treated as supervised breach-risk modeling using observed lifecycle outcomes, not as fraud classification.

### Pending verification (not yet classified as in-scope or out-of-scope)

- Whether the March 2026 eSAKSHI public dashboard revamp exposes vendor identity or only aggregate payment amounts — resolves FR-08's vendor-concentration question and whether vendor-level payment-stage anomaly detection is buildable.
- Whether the PS-owning organization (MoSPI/DIID) can provide de-identified vendor-identity or payment-stage sample data directly through the SIH mentor channel — the standard path to unblock FR-08 and payment-stage detection if the public dashboard does not expose it. Mentor access is a normal part of the SIH process, not a workaround.

---

## Definition of Done

There are two definitions, deliberately separate, so "done" is never ambiguous about whether ML has been built yet.

### Phase 0–3 Definition of Done (rule/statistical core)

MPLADS data

→ normalized work lifecycle

→ baseline comparison

→ rule and statistical anomaly detectors

→ cross-work / entity analysis

→ trend analysis

→ composite risk assessment (rule/statistical signals only)

→ evidence-backed explanation

→ recommended next review action

→ ranked review priorities

This is a complete, demoable system on its own. It does not include any trained model output.

### Final Definition of Done (Phase 0–4, integrated system)

Everything above, plus:

→ trained unsupervised anomaly ensemble (Component A)

→ trained supervised breach-risk model (Component B)

→ temporal-holdout evaluation metrics for Component B

→ persisted model artifacts and reproducibility metadata

→ both integrated into the composite risk score alongside the rule/statistical signals

The resulting product is:

> **An explainable MPLADS anomaly and risk-prioritization engine that identifies unusual works, explains the evidence behind each finding, and prioritizes cases for human review.**

It is not a fraud-verdicting system. Do not treat the Phase 0–3 definition as the final product, and do not treat the final Definition of Done as license to start Phase 4 work before Phases 0–3 are frozen and validated.

---

## References

- **SIH26102 Problem Statement** — expected anomaly, trend, compliance and risk-detection capabilities. (sih-explorer.amanuniyal47.workers.dev)
- **MoSPI, 6 March 2026** — current eSAKSHI workflow, public dashboard and historical coverage limitations. ([pib.gov.in](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2235932&lang=2&reg=3))
- **MPLADS Guidelines 2023** — operational and compliance requirements. ([mplads.gov.in](https://www.mplads.gov.in/MPLADS/En/2034.aspx))
