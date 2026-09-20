# MPLADS Intelligence Engine

## Core Prototype — Project Specification & Implementation Guide

**Problem:** SIH26102 / PS102
**Scope:** Analytical core only
**Status:** Implementation baseline

---

## Requirements / Constraints

### Objective

Build an independent analytical engine that consumes available MPLADS/eSAKSHI records and produces **ranked, explainable anomalies and review priorities**.

The core shall address:

* expenditure and utilization anomalies;
* cost anomalies / overruns;
* execution and timeline anomalies;
* potentially duplicate or highly similar works;
* unusual vendor / Implementing Agency patterns;
* aggregate trends;
* combinations of multiple weak signals.

This corresponds to the SIH requirement for identifying trends, anomalies, irregularities, potential fraud, cost overruns, duplicate works, delayed projects, deviations from norms and risk-based alerts across MPLADS data.

### Constraints

* Independent of frontend/backend.
* No detector may silently depend on unavailable data.
* Missing/incomplete data must be explicit.
* Anomalies must not be presented as confirmed fraud or wrongdoing.
* Every high-priority finding must have evidence and explanation.
* Regulatory deviations and statistical anomalies must remain distinct.
* Detectors must be modular and independently testable.
* Thresholds, peer definitions and risk weights must be configurable.
* Historical comparisons must account for data-coverage differences.

eSAKSHI provides integrated recommendation, sanction, execution/progress and payment workflows from April 2023 onward, while MoSPI documents limitations in earlier online coverage. ([pib.gov.in](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2235932&lang=2&reg=3&utm_source=chatgpt.com))

---

## Implementation Guidelines

### Preferred approach

Use a **hybrid, explainable anomaly-detection architecture**:

**deterministic rules → statistical analysis → cross-record analysis → multivariate anomaly detection → composite risk assessment**

### Detection philosophy

* **Rules:** explicit MPLADS/process deviations.
* **Statistics:** unusual behaviour relative to peer or historical baselines.
* **Similarity:** potentially duplicated/highly similar works.
* **Relationships:** unusual vendor/agency/entity patterns.
* **Trends:** meaningful aggregate changes over time.
* **ML:** unusual combinations of otherwise interpretable characteristics.

ML is a supporting signal, not the final authority.

### Design rules

* Prefer simple, explainable methods.
* Compare against appropriate peers, not global averages.
* Preserve evidence behind every finding.
* Make policy values configurable.
* Separate observed facts, comparisons and inferred anomalies.
* Design around actually available data.
* Start with structured data.
* Optimize for **review prioritization**, not binary fraud classification.

MPLADS guidelines include explicit operational constraints such as sanction/rejection timelines and generally no more than one year for completion; these should be represented as configurable policy rules. ([mplads.gov.in](https://www.mplads.gov.in/MPLADS/En/2034.aspx?utm_source=chatgpt.com))

---

## Architecture

```text id="fp9u8l"
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

* identity, description and category;
* location and administrative context;
* MP / constituency;
* recommendation;
* sanction;
* cost;
* expenditure;
* payments;
* progress;
* completion;
* Implementing Agency;
* vendor/payee;
* supporting evidence.

Secondary entities include:

**MP → Work → Implementing Agency → Vendor → Payment**

### Lifecycle

**Recommendation → Sanction → Execution → Progress → Payments → Completion**

This reflects the current eSAKSHI workflow. ([pib.gov.in](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2235932&lang=2&reg=3&utm_source=chatgpt.com))

---

## Functional Requirements

### FR-01 — Data Foundation

Normalize source datasets; handle inconsistent fields, dates, financial values, identifiers, missing data, duplicate/aggregate rows and other data-quality issues.

### FR-02 — Work Reconstruction

Associate records referring to the same work and reconstruct its available lifecycle.

### FR-03 — Baselines

Provide:

* **regulatory** baselines from MPLADS rules;
* **peer** baselines for comparable works;
* **historical/behavioural** baselines where coverage permits.

### FR-04 — Compliance Detection

Detect configurable deviations such as delayed sanction/rejection, prolonged completion, financial inconsistencies, missing lifecycle transitions and other identifiable procedural deviations.

### FR-05 — Financial Anomaly Detection

Detect:

* unusual project costs;
* peer-group cost outliers;
* abnormal utilization;
* expenditure inconsistent with sanction;
* unusual payment patterns;
* unusual temporal concentration of payments.

### FR-06 — Execution Anomaly Detection

Detect:

* delayed works;
* stalled works;
* unusually long execution;
* progress/expenditure mismatch;
* inconsistent lifecycle states.

### FR-07 — Similarity / Duplicate Detection

Identify candidate duplicate or highly similar works using combinations of description, location, category, cost, time and administrative context.

Output is a **review candidate**, not a declaration of duplication or fraud.

### FR-08 — Relationship Analysis

Identify unusual:

* vendor concentration;
* agency concentration;
* recurrence of entities across anomalies;
* combinations of related works/entities.

### FR-09 — Trend Analysis

Identify meaningful changes over time at relevant levels such as state, district, constituency, agency, vendor, work category and financial year.

### FR-10 — Multivariate Anomaly Detection

Identify unusual combinations of features that may not trigger individual detectors.

### FR-11 — Risk Assessment

Combine detector outputs into configurable review-priority levels:

* Normal
* Low
* Medium
* High

Component signals must remain visible.

### FR-12 — Explainability

Every significant finding must state:

* what was detected;
* observed values;
* comparison/baseline;
* deviation/similarity strength;
* related records/entities;
* relevant limitations.

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

* use only required information;
* preserve source provenance;
* do not modify source records;
* keep outputs traceable;
* do not infer unsupported intent or personal attributes.

---

## Implementation Plan

### Phase 0 — Data Foundation & Analytical Model

**Goal:** Establish what can actually be built and create the unified analytical foundation.

* Obtain and audit representative MPLADS/eSAKSHI datasets.
* Inventory fields, identifiers, coverage and relationships.
* Identify missing/incomplete information and feasible detectors.
* Normalize records, including dates, financial values, identifiers, duplicates and aggregates.
* Define the canonical **Work** representation.
* Reconstruct the available work lifecycle.
* Establish MP, work, Implementing Agency, vendor and payment relationships.
* Implement explicit data-quality and missing-data handling.

**Deliverable:** Unified analytical dataset + Data Map + Coverage Matrix.

---

### Phase 1 — Baselines & Core Detection

**Goal:** Establish comparison baselines and implement the primary anomaly detectors.

* Encode relevant MPLADS/process rules as configurable policy baselines.
* Establish appropriate peer groups.
* Calculate historical/behavioural baselines where coverage permits.
* Define minimum sample requirements.
* Implement:

  1. Compliance detection
  2. Financial anomaly detection
  3. Execution/timeline anomaly detection
* Each detector produces:
  **Finding + Severity + Evidence + Explanation**.

**Deliverable:** Baseline specification + independent core detector outputs.

---

### Phase 2 — Cross-Work, Entity & Pattern Intelligence

**Goal:** Detect signals that require relationships across works, entities or time.

* Implement similarity / duplicate-work detection.
* Implement vendor / Implementing Agency relationship and concentration analysis.
* Identify recurrence of entities across anomalous works.
* Implement aggregate trend analysis covering:

  * anomaly rates;
  * costs;
  * delays;
  * expenditure;
  * recurring entity patterns.
* Add unsupervised multivariate anomaly detection as a **supporting signal**.

**Deliverable:** Cross-record findings + trend findings + multivariate anomaly output.

---

### Phase 3 — Risk, Explainability & Validation

**Goal:** Convert detector outputs into stable, reviewable and validated priorities.

* Establish configurable component scores, detector weights and risk levels.
* Incorporate confidence and data-quality handling.
* Combine detector outputs into unified review priorities.
* Ensure every significant finding answers:
  **What happened? Why is it unusual? Compared with what? What evidence supports it? What are the limitations?**
* Validate against:

  * normal works;
  * cost anomalies;
  * timeline anomalies;
  * duplicate-like works;
  * payment anomalies;
  * relationship anomalies;
  * multi-signal cases;
  * ambiguous/legitimate exceptions.
* Test controlled anomaly injection.
* Document data limitations and detector behaviour.
* Freeze the core once risk aggregation is stable, outputs are explainable, validation passes and demonstration scenarios work end-to-end.

**Deliverable:** Validated, explainable, configurable MPLADS review-prioritization engine.

---

## Acceptance Criteria

The core is complete when:

### AC-01

Representative MPLADS data can be analysed end-to-end.

### AC-02

Available records can be reconstructed into work lifecycles.

### AC-03

Relevant compliance deviations can be detected.

### AC-04

Financial anomalies can be identified against appropriate baselines.

### AC-05

Execution/timeline anomalies can be detected.

### AC-06

Potentially similar/duplicate works can be surfaced.

### AC-07

Unusual vendor/agency concentration patterns can be identified.

### AC-08

Meaningful aggregate trends can be surfaced.

### AC-09

A supporting multivariate anomaly signal can be generated.

### AC-10

Detector outputs can be combined into configurable review-priority levels.

### AC-11

Every high-priority result contains concrete evidence and explanation.

### AC-12

Anomalies are never presented as confirmed fraud or intentional wrongdoing.

### AC-13

Controlled anomalies can be injected and detected.

### AC-14

Important data limitations are surfaced rather than silently ignored.

---

## Out of Scope / Deferred

### Core exclusions

* frontend;
* dashboards;
* backend/API;
* authentication/user management;
* production database;
* cloud deployment;
* mobile application;
* autonomous case decisions.

### Deferred analytical capabilities

* OCR;
* document understanding;
* image verification/reuse detection;
* satellite imagery;
* GPS/site verification;
* advanced graph ML;
* predictive completion forecasting;
* automated investigation workflows;
* external-data enrichment;
* richer evidence analysis.

These should be considered only after the structured-data core is validated.

---

## Core Definition of Done

The core must support:

**MPLADS data**

→ **normalized work lifecycle**

→ **baseline comparison**

→ **multiple independent anomaly detectors**

→ **cross-work / entity analysis**

→ **trend analysis**

→ **multivariate anomaly signal**

→ **composite risk assessment**

→ **evidence-backed explanation**

→ **ranked review priorities**

The resulting product is:

> **An explainable MPLADS anomaly and risk-prioritization engine that identifies unusual works, explains the evidence behind each finding, and prioritizes cases for human review.**

It is not a fraud-verdicting system.

---

## References

* **SIH26102 Problem Statement** — expected anomaly, trend, compliance and risk-detection capabilities. ([sih-explorer.amanuniyal47.workers.dev](https://sih-explorer.amanuniyal47.workers.dev/problem/SIH26102))
* **MoSPI, 6 March 2026** — current eSAKSHI workflow, public dashboard and historical coverage limitations. ([pib.gov.in](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2235932&lang=2&reg=3&utm_source=chatgpt.com))
* **MPLADS Guidelines 2023** — operational and compliance requirements. ([mplads.gov.in](https://www.mplads.gov.in/MPLADS/UploadedFiles/MPLADSGuidelines2023_English_.pdf?utm_source=chatgpt.com))
