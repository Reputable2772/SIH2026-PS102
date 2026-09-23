"""
Compliance Anomaly Detectors.

Enforces statutory MPLADS Guidelines 2023 and ministerial monitoring standards:
D1: Sanction turnaround SLA (>45 days)
D2: Prolonged execution (>1 year general / >540 days RS exception)
D3: Stalled disbursement (>90 days without initial disbursement)
D4: Irregular lifecycle sequence (retroactive sanctions, pre-sanction disbursements)
"""

from typing import List, Optional
import pandas as pd
import numpy as np
from src.config import POLICY
from src.engine.detectors.base import BaseDetector, Finding, AnomalyCategory


class SanctionSLABreachDetector(BaseDetector):
    """Detects works where recommendation-to-sanction turnaround exceeds 45 days."""

    def __init__(self, sla_days: int = POLICY.SANCTION_SLA_DAYS):
        super().__init__(
            code="COMP-D1",
            name="Sanction Turnaround SLA Breach",
            category=AnomalyCategory.COMPLIANCE
        )
        self.sla_days = sla_days

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        # Filter to works with valid positive recommendation-to-sanction duration
        mask = (df_works["days_rec_to_sanction"] > self.sla_days)
        flagged = df_works[mask]

        findings = []
        for _, row in flagged.iterrows():
            days = float(row["days_rec_to_sanction"])
            overage = days - self.sla_days
            # Severity scales from 0.1 at 46 days to 0.60 at 365+ days overage (calibrated procedural SLA ceiling)
            sev = float(np.clip(0.1 + (overage / 365.0) * 0.5, 0.1, 0.60))
            conf = float(np.clip(row.get("dqi_score", 0.8), 0.3, 1.0))
            
            work_id = str(row.get("WORK_ID") or row.get("WORK_RECOMMENDATION_DTL_ID"))
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
            
            f = Finding(
                finding_id=f"FIND-D1-{rec_id}",
                work_id=work_id,
                work_rec_id=rec_id,
                detector_code=self.code,
                detector_name=self.name,
                category=self.category,
                severity=sev,
                confidence=conf,
                evidence={
                    "days_rec_to_sanction": days,
                    "statutory_limit_days": self.sla_days,
                    "overage_days": overage,
                    "recommendation_date": str(row["RECOMMENDATION_DATE"]),
                    "sanction_date": str(row["SANCTION_DATE"])
                },
                explanation=(
                    f"Work proposal required {int(days)} days from recommendation to sanction, "
                    f"exceeding the statutory 45-day deadline under MPLADS Guidelines Para 3.2.4 by {int(overage)} days."
                ),
                next_review_action=(
                    "Issue compliance inquiry to Implementing District Authority (IDA) to record administrative reasons for "
                    "delayed approval and confirm whether Model Code of Conduct exemption applied."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0))
            )
            findings.append(f)
        return findings


class ExecutionDeadlineDetector(BaseDetector):
    """Detects works taking longer than 1 year (or 540 days for RS) to complete or reach milestone."""

    def __init__(self, ls_sla: int = POLICY.EXECUTION_SLA_DAYS, rs_sla: int = POLICY.RS_POST_TENURE_SLA_DAYS):
        super().__init__(
            code="COMP-D2",
            name="Execution Deadline SLA Breach",
            category=AnomalyCategory.COMPLIANCE
        )
        self.ls_sla = ls_sla
        self.rs_sla = rs_sla

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        findings = []
        if "ACTUAL_END_DATE" not in df_works.columns or "house" not in df_works.columns:
            return []

        # Check completed works
        if "days_sanction_to_completion" in df_works.columns:
            completed = df_works[df_works["ACTUAL_END_DATE"].notna()].copy()
            ls_over = completed[(completed["house"] == "LOK_SABHA") & (completed["days_sanction_to_completion"] > self.ls_sla)]
            rs_over = completed[(completed["house"] == "RAJYA_SABHA") & (completed["days_sanction_to_completion"] > self.rs_sla)]
        else:
            ls_over = pd.DataFrame()
            rs_over = pd.DataFrame()

        # Check in-progress works that have already surpassed the SLA
        if "SANCTION_DATE" in df_works.columns and "days_since_sanction" in df_works.columns:
            ongoing = df_works[df_works["ACTUAL_END_DATE"].isna() & df_works["SANCTION_DATE"].notna()].copy()
            ls_ong_over = ongoing[(ongoing["house"] == "LOK_SABHA") & (ongoing["days_since_sanction"] > self.ls_sla)]
            rs_ong_over = ongoing[(ongoing["house"] == "RAJYA_SABHA") & (ongoing["days_since_sanction"] > self.rs_sla)]
        else:
            ls_ong_over = pd.DataFrame()
            rs_ong_over = pd.DataFrame()

        all_flagged = pd.concat([ls_over, rs_over, ls_ong_over, rs_ong_over], ignore_index=True)

        for _, row in all_flagged.iterrows():
            is_comp = pd.notna(row["ACTUAL_END_DATE"])
            duration = float(row["days_sanction_to_completion"]) if is_comp else float(row["days_since_sanction"])
            sla = self.rs_sla if row["house"] == "RAJYA_SABHA" else self.ls_sla
            overage = duration - sla

            sev = float(np.clip(0.2 + (overage / 365.0) * 0.8, 0.2, 1.0))
            conf = float(np.clip(row.get("dqi_score", 0.8), 0.3, 1.0))

            work_id = str(row.get("WORK_ID") or row.get("WORK_RECOMMENDATION_DTL_ID"))
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
            status_str = "completed" if is_comp else "ongoing (incomplete)"

            f = Finding(
                finding_id=f"FIND-D2-{rec_id}",
                work_id=work_id,
                work_rec_id=rec_id,
                detector_code=self.code,
                detector_name=self.name,
                category=self.category,
                severity=sev,
                confidence=conf,
                evidence={
                    "status": status_str,
                    "duration_days": duration,
                    "statutory_limit_days": sla,
                    "overage_days": overage,
                    "sanction_date": str(row["SANCTION_DATE"]),
                    "completion_date": str(row["ACTUAL_END_DATE"]) if is_comp else "Not Completed"
                },
                explanation=(
                    f"Work is {status_str} with {int(duration)} days elapsed since sanction, "
                    f"exceeding the statutory {sla}-day execution ceiling under Para 3.2.12 by {int(overage)} days."
                ),
                next_review_action=(
                    "Direct Implementing Agency (IA) to submit physical inspection log, assess contractor liquidated damages, "
                    "and review whether time extension was formally sanctioned with written justification."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0))
            )
            findings.append(f)

        return findings


class StalledDisbursementDetector(BaseDetector):
    """Detects works with zero disbursement 90+ days after sanction."""

    def __init__(self, stall_days: int = POLICY.DISBURSEMENT_STALL_DAYS):
        super().__init__(
            code="COMP-D3",
            name="Stalled Initial Disbursement",
            category=AnomalyCategory.COMPLIANCE
        )
        self.stall_days = stall_days

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        if "SANCTION_DATE" not in df_works.columns or "days_since_sanction" not in df_works.columns:
            return []

        # Filter to works sanctioned 90+ days ago with zero or missing disbursement and not marked completed
        disb_s = df_works["total_disbursed"].fillna(0.0) if "total_disbursed" in df_works.columns else pd.Series(0.0, index=df_works.index)
        has_end = "ACTUAL_END_DATE" in df_works.columns
        mask = (
            (df_works["SANCTION_DATE"].notna()) &
            (df_works["days_since_sanction"] > self.stall_days) &
            (disb_s <= 0) &
            (df_works["ACTUAL_END_DATE"].isna() if has_end else pd.Series(True, index=df_works.index))
        )
        flagged = df_works[mask]

        findings = []
        for _, row in flagged.iterrows():
            days_stalled = float(row["days_since_sanction"])
            overage = days_stalled - self.stall_days
            sev = float(np.clip(0.3 + (overage / 180.0) * 0.7, 0.3, 1.0))
            conf = float(np.clip(row.get("dqi_score", 0.8), 0.3, 1.0))

            work_id = str(row.get("WORK_ID") or row.get("WORK_RECOMMENDATION_DTL_ID"))
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])

            disb_val = row.get("total_disbursed")
            has_exp = row.get("has_expenditure_record", False)
            disb_float = float(disb_val) if pd.notna(disb_val) else 0.0
            is_missing_exp = pd.isna(disb_val) or not bool(has_exp)
            disb_desc = "no expenditure vouchers logged" if is_missing_exp else f"₹{disb_float:,.0f} disbursed"

            f = Finding(
                finding_id=f"FIND-D3-{rec_id}",
                work_id=work_id,
                work_rec_id=rec_id,
                detector_code=self.code,
                detector_name=self.name,
                category=self.category,
                severity=sev,
                confidence=conf,
                evidence={
                    "days_since_sanction": days_stalled,
                    "stall_threshold_days": self.stall_days,
                    "total_disbursed": disb_float,
                    "has_expenditure_record": bool(has_exp),
                    "is_missing_expenditure": is_missing_exp,
                    "sanction_date": str(row["SANCTION_DATE"])
                },
                explanation=(
                    f"Work has had zero confirmed disbursements ({disb_desc}) across {int(days_stalled)} days following sanction, "
                    f"breaching the 90-day ministerial dormancy monitoring threshold."
                ),
                next_review_action=(
                    "Issue show-cause inquiry to District Authority to determine whether tender was awarded, "
                    "site was encumbered, or funds should be surrendered to the unallocated MP quota."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0))
            )
            findings.append(f)

        return findings


class LifecycleLeapDetector(BaseDetector):
    """Detects irregular lifecycle sequencing (retroactive dates, disbursement before sanction)."""

    def __init__(self):
        super().__init__(
            code="COMP-D4",
            name="Irregular Lifecycle Sequence",
            category=AnomalyCategory.COMPLIANCE
        )

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        is_retro = df_works["is_retroactive_sanction"] == True if "is_retroactive_sanction" in df_works.columns else pd.Series(False, index=df_works.index)
        is_comp = df_works["is_completion_before_sanction"] == True if "is_completion_before_sanction" in df_works.columns else pd.Series(False, index=df_works.index)
        is_disb = df_works["is_disbursement_before_sanction"] == True if "is_disbursement_before_sanction" in df_works.columns else pd.Series(False, index=df_works.index)
        mask = is_retro | is_comp | is_disb
        flagged = df_works[mask]

        findings = []
        for _, row in flagged.iterrows():
            details = []
            if row.get("is_retroactive_sanction", False):
                details.append("Sanction date precedes recommendation date")
            if row.get("is_completion_before_sanction", False):
                details.append("Completion date recorded before sanction date")
            if row.get("is_disbursement_before_sanction", False):
                details.append("Disbursement voucher recorded before sanction date")

            work_id = str(row.get("WORK_ID") or row.get("WORK_RECOMMENDATION_DTL_ID"))
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])

            f = Finding(
                finding_id=f"FIND-D4-{rec_id}",
                work_id=work_id,
                work_rec_id=rec_id,
                detector_code=self.code,
                detector_name=self.name,
                category=self.category,
                severity=0.85,
                confidence=0.90,
                evidence={
                    "irregularities": details,
                    "recommendation_date": str(row["RECOMMENDATION_DATE"]),
                    "sanction_date": str(row["SANCTION_DATE"]),
                    "actual_end_date": str(row.get("ACTUAL_END_DATE")),
                    "first_payment_date": str(row.get("first_payment_date"))
                },
                explanation=(
                    f"Lifecycle chronology violation detected: {'; '.join(details)}. "
                    "Indicates post-facto regularization or severe back-dating."
                ),
                next_review_action=(
                    "Demand administrative audit trail and original physical dispatch register from District Magistrate "
                    "to confirm authenticity of approval dates."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0))
            )
            findings.append(f)

        return findings
