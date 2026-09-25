"""
Catalog of Autonomous Anomaly Detectors & Statutory Rule Matrix.
"""

from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter(prefix="/detectors", tags=["Detector Glossary & Statutory Rules"])

DETECTORS_CATALOG: List[Dict[str, Any]] = [
    {
        "code": "COMP-D1",
        "name": "Sanction SLA Breach",
        "category": "COMPLIANCE",
        "phase": "Phase 1",
        "legal_basis": "MPLADS Guidelines 2023, Para 3.2.4",
        "threshold": "> 45 calendar days from MP recommendation",
        "formula": "days_rec_to_sanction > 45",
        "description": "Mandates that District Authority (IDA) must issue administrative sanction or formal rejection within 45 days of receiving MP recommendation.",
        "prescribed_action": "Issue compliance notice to District Planning Officer; require written justification for delayed administrative sanction.",
    },
    {
        "code": "COMP-D2",
        "name": "Execution Deadline Breach",
        "category": "COMPLIANCE",
        "phase": "Phase 1",
        "legal_basis": "MPLADS Guidelines 2023, Para 3.2.12",
        "threshold": "> 365 calendar days (540 days for Rajya Sabha post-tenure)",
        "formula": "days_since_sanction > SLA and actual_end_date is null",
        "description": "Mandates project completion within 1 year of administrative sanction under normal statutory cycles.",
        "prescribed_action": "Dispatch District Quality Monitor (DQM) for physical milestone verification; impose administrative penalty on defaulting agency.",
    },
    {
        "code": "COMP-D3",
        "name": "Stalled Initial Disbursement",
        "category": "COMPLIANCE",
        "phase": "Phase 1",
        "legal_basis": "Ministerial Monitoring Criterion / Para 4.1",
        "threshold": "> 90 calendar days without initial mobilization payment",
        "formula": "days_since_sanction > 90 and total_disbursed == 0",
        "description": "Flags works that have received administrative sanction but remain completely dormant without first payment or contractor mobilization.",
        "prescribed_action": "Verify tender award status; confirm whether holding account funds were allocated or administrative revocation is required.",
    },
    {
        "code": "COMP-D4",
        "name": "Lifecycle Leap / Sequence Irregularity",
        "category": "COMPLIANCE",
        "phase": "Phase 1",
        "legal_basis": "Statutory Administrative Order & PFMS Workflow Rules",
        "threshold": "Disbursement before sanction date OR completion before sanction date",
        "formula": "days_sanction_to_first_payment < 0 or days_sanction_to_completion < 0",
        "description": "Detects impossible chronological milestone progressions indicating post-facto book entries or data back-filling.",
        "prescribed_action": "Initiate administrative integrity inquiry on data entry operator; cross-examine physical measurement book (MB) dates against PFMS voucher dates.",
    },
    {
        "code": "FIN-D5",
        "name": "Cost Peer Group Outlier",
        "category": "FINANCIAL",
        "phase": "Phase 1",
        "legal_basis": "Statistical Baseline Comparison / Schedule of Rates (SoR)",
        "threshold": "Z-score >= 2.5 above State & Category Peer Median",
        "formula": "(sanction_amount - peer_median) / peer_std >= 2.5",
        "description": "Identifies budget estimates that excessively diverge from historical unit costs for identical asset categories in the same state.",
        "prescribed_action": "Re-examine Detailed Project Report (DPR) and technical sanction rates against State PWD Schedule of Rates.",
    },
    {
        "code": "FIN-D6",
        "name": "Expenditure Budget Overrun",
        "category": "FINANCIAL",
        "phase": "Phase 1",
        "legal_basis": "General Financial Rules (GFR) / MPLADS Para 3.2.14",
        "threshold": "Total Disbursed > 105% of Administrative Sanction",
        "formula": "total_disbursed > sanction_amount * 1.05",
        "description": "Flags unauthorized fiscal drawdowns exceeding approved sanction budget without formal revised technical sanction.",
        "prescribed_action": "Halt further voucher clearance; mandate Implementing Agency to submit revised technical justification.",
    },
    {
        "code": "FIN-D8",
        "name": "Temporal Disbursement Surge",
        "category": "FINANCIAL",
        "phase": "Phase 1",
        "legal_basis": "Financial Velocity & Year-End March Rush Monitoring",
        "threshold": "> 70% of total lifetime funds drawn within single 30-day window",
        "formula": "quarterly_velocity >= 0.70 * total_disbursed",
        "description": "Detects artificial velocity surges or clustered payments often associated with fiscal year-end budget exhaust behavior.",
        "prescribed_action": "Audit measurement book vouchers for stage-completion alignment.",
    },
    {
        "code": "EXEC-D9",
        "name": "Progress-Expenditure Mismatch",
        "category": "EXECUTION",
        "phase": "Phase 1",
        "legal_basis": "Physical Asset Handover Mandate / Para 3.2.13",
        "threshold": "Disbursed >= 85% and Age > 365 days with No Completion Certificate",
        "formula": "disbursed_ratio >= 0.85 and days_since_sanction > 365 and end_date is null",
        "description": "Detects works that have drawn nearly all allocated funds but have stalled without formal handover or completion certification.",
        "prescribed_action": "Dispatch Executive Magistrate or DQM for physical inspection; impound contractor final bill pending site handover.",
    },
    {
        "code": "AGY-D11",
        "name": "Implementing Agency Capacity Overload",
        "category": "AGENCY",
        "phase": "Phase 1",
        "legal_basis": "Operational Governance & District Capacity Management",
        "threshold": ">= 10 delayed unfinished works and >= 50 Lakhs committed backlog",
        "formula": "agency_delayed_count >= 10 and agency_backlog >= 5,000,000",
        "description": "Surfaces bottlenecked Implementing Agencies overburdened with uncompleted projects across multiple constituencies.",
        "prescribed_action": "Enforce administrative moratorium on awarding new works to this agency; reassign delayed works to alternative engineering wings.",
    },
    {
        "code": "SIM-D12",
        "name": "Duplicate Work / Scope Similarity",
        "category": "NETWORK_SIMILARITY",
        "phase": "Phase 2",
        "legal_basis": "MPLADS Prohibition on Duplicate Asset Funding / Para 2.4",
        "threshold": "Cosine Similarity >= 0.82 with matching cost window (+/- 20%)",
        "formula": "TF-IDF(desc1, desc2) >= 0.82 and cost_diff_ratio <= 0.20",
        "description": "Detects identical or near-duplicate work proposals in the same district, mitigating duplicate billing for existing infrastructure.",
        "prescribed_action": "Conduct field verification of GPS coordinates and photographic completion evidence to confirm two distinct physical assets.",
    },
    {
        "code": "AGY-D13",
        "name": "District Agency Monopolization",
        "category": "AGENCY",
        "phase": "Phase 2",
        "legal_basis": "Competitive Public Procurement & Antitrust Norms",
        "threshold": "District HHI >= 2,500 OR Single Agency captures > 40% of district volume",
        "formula": "HHI = sum(shares^2) >= 2500 or max(share) >= 0.40",
        "description": "Surfaces market concentration where one agency or contractor captures an excessive share of district MPLADS execution.",
        "prescribed_action": "Review whether local statutory rules designate a single nodal agency, or mandate diversification of implementing agencies.",
    },
    {
        "code": "VND-D14",
        "name": "Vendor Payment Monopolization",
        "category": "NETWORK_SIMILARITY",
        "phase": "Phase 2",
        "legal_basis": "Anti-Collusion & Fair Procurement Competition",
        "threshold": "Single vendor capturing > 50% of total district disbursed funds",
        "formula": "vendor_disbursed_share >= 0.50 and works_count >= 5",
        "description": "Identifies vendor capture and potential contractor favoritism in district-level execution.",
        "prescribed_action": "Audit district tendering records to verify open competitive bidding compliance.",
    },
    {
        "code": "REC-D15",
        "name": "Systemic Entity Recurrence",
        "category": "NETWORK_SIMILARITY",
        "phase": "Phase 2",
        "legal_basis": "Empirical Bayes Shrinkage / Reputational Integrity",
        "threshold": "Posterior delay breach probability significantly exceeds national prior",
        "formula": "theta_EB = (k + alpha) / (n + alpha + beta) with Beta-Binomial prior",
        "description": "Distinguishes systemic contractor failure from chance variations by applying Bayesian shrinkage to vendor track records.",
        "prescribed_action": "Disqualify habitually defaulting contractors from upcoming district tender pre-qualifications.",
    },
    {
        "code": "ML-UNSUP",
        "name": "Unsupervised Multi-Stage Outlier Ensemble",
        "category": "ML_SUPPORTING",
        "phase": "Phase 4",
        "legal_basis": "Data-Driven Anomaly Discovery",
        "threshold": "Isolation Forest Anomaly Score >= 0.65",
        "formula": "Score = -E(h(x)) across 100 Isolation Trees",
        "description": "Detects subtle, multi-dimensional anomalies across recommendation, sanction, and payment phases simultaneously.",
        "prescribed_action": "Review multi-dimensional evidence card in governance dossier.",
    },
    {
        "code": "ML-BREACH",
        "name": "Early-Warning Completion Breach Predictor",
        "category": "ML_SUPPORTING",
        "phase": "Phase 4",
        "legal_basis": "Predictive Project Risk Management",
        "threshold": "Predicted Probability of 1-Year SLA Breach >= 70%",
        "formula": "P(Breach = 1 | Sanction-time features) via HistGradientBoosting",
        "description": "Forecasts risk of severe delay at the very moment of sanction approval before substantial capital is committed.",
        "prescribed_action": "Establish bi-weekly progress oversight checkpoints with Implementing Agency from inception.",
    },
]


import pandas as pd
from fastapi import Depends
from pydantic import BaseModel

from backend.core.auth import UserProfile, get_tenant_scope, require_any_permission
from backend.services.data_service import DataService


class SimulationRequest(BaseModel):
    sla_days: int = 45
    execution_days: int = 365
    z_threshold: float = 2.5


@router.get("", response_model=List[Dict[str, Any]])
def list_all_detectors():
    """Returns the comprehensive catalog of all 15 anomaly detectors with statutory rules."""
    return DETECTORS_CATALOG


@router.post("/simulate", response_model=Dict[str, Any])
def simulate_thresholds(
    payload: SimulationRequest,
    user: UserProfile = Depends(
        require_any_permission(
            "admin_config",
            "trigger_audit",
            "read_all",
            "simulate_thresholds",
            "manage_district_review_queue",
            "review_state_works",
        )
    ),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Dynamically simulates changing statutory thresholds across works (Guarded by RBAC & Tenant Scoping)."""
    ds = DataService.get_instance()
    df = ds.apply_tenant_filter(ds.df_works, scope)

    if df.empty:
        return {
            "total_works": 0,
            "parameters": payload.model_dump(),
            "sanction_sla_breaches": 0,
            "execution_sla_breaches": 0,
            "stalled_works": 0,
            "budget_overruns": 0,
            "peer_cost_outliers": 0,
            "simulated_critical_count": 0,
            "simulated_high_count": 0,
        }

    days_rec = pd.to_numeric(
        df["days_rec_to_sanction"] if "days_rec_to_sanction" in df.columns else pd.Series(0, index=df.index),
        errors="coerce",
    ).fillna(0)
    days_sanc = pd.to_numeric(
        df["days_since_sanction"] if "days_since_sanction" in df.columns else pd.Series(0, index=df.index),
        errors="coerce",
    ).fillna(0)
    has_end = (
        df["ACTUAL_END_DATE"].notna() if "ACTUAL_END_DATE" in df.columns else pd.Series(False, index=df.index)
    )
    sanc = pd.to_numeric(df["SANCTION_AMOUNT"], errors="coerce").fillna(0.0)
    disb = pd.to_numeric(df["total_disbursed"], errors="coerce").fillna(0.0)

    # Z-threshold cost outlier calculation across works
    sanc_mean = float(sanc.mean())
    sanc_std = float(sanc.std())
    if pd.isna(sanc_std) or sanc_std == 0:
        cost_outliers = pd.Series(False, index=df.index)
    else:
        z_scores = (sanc - sanc_mean) / sanc_std
        cost_outliers = z_scores > payload.z_threshold

    mask_sla = days_rec > payload.sla_days
    mask_exec = (days_sanc > payload.execution_days) & (~has_end)
    mask_stalled = (sanc > 0) & (disb == 0) & (days_sanc > 90)
    mask_overrun = (sanc > 0) & (disb > sanc * 1.05)

    sla_breaches = int(mask_sla.sum())
    exec_breaches = int(mask_exec.sum())
    stalled_works = int(mask_stalled.sum())
    overruns = int(mask_overrun.sum())
    peer_cost_outliers = int(cost_outliers.sum())

    # Critical conditions: severe overrun or stalled for 2x statutory execution period
    mask_crit = (sanc > 0) & (mask_overrun | ((days_sanc > payload.execution_days * 2) & (~has_end)))
    sim_crit = int(mask_crit.sum())

    # High priority: non-critical SLA breaches, execution delays, stalled works, or cost outliers
    mask_high = (mask_sla | mask_exec | mask_stalled | cost_outliers) & (~mask_crit)
    sim_high = int(mask_high.sum())

    return {
        "total_works": len(df),
        "parameters": payload.model_dump(),
        "sanction_sla_breaches": sla_breaches,
        "execution_sla_breaches": exec_breaches,
        "stalled_works": stalled_works,
        "budget_overruns": overruns,
        "peer_cost_outliers": peer_cost_outliers,
        "simulated_critical_count": sim_crit,
        "simulated_high_count": sim_high,
    }
