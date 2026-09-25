"""
Execution and Lifecycle Progress Anomaly Detectors.

Detects progress vs expenditure mismatches, chronic project stagnation,
and lifecycle state regressions.
"""

from typing import List, Optional

import numpy as np
import pandas as pd

from src.config import POLICY
from src.engine.detectors.base import AnomalyCategory, BaseDetector, Finding, safe_float


class ProgressExpenditureMismatchDetector(BaseDetector):
    """Detects works with near-total disbursement (>85%) and severe age (>365d) but no completion."""

    def __init__(self, min_ratio: float = 0.85, min_days: int = POLICY.EXECUTION_SLA_DAYS):
        super().__init__(code="EXEC-D9", name="Progress-Expenditure Mismatch", category=AnomalyCategory.EXECUTION)
        self.min_ratio = min_ratio
        self.min_days = min_days

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        if "SANCTION_AMOUNT" not in df_works.columns or "days_since_sanction" not in df_works.columns:
            return []
        has_end = "ACTUAL_END_DATE" in df_works.columns
        disb_s = (
            df_works["total_disbursed"].fillna(0.0)
            if "total_disbursed" in df_works.columns
            else pd.Series(0.0, index=df_works.index)
        )
        mask = (
            (df_works["SANCTION_AMOUNT"] > 0)
            & (df_works["total_disbursed"].notna() if "total_disbursed" in df_works.columns else False)
            & (disb_s >= df_works["SANCTION_AMOUNT"] * self.min_ratio)
            & (df_works["days_since_sanction"] > self.min_days)
            & (df_works["ACTUAL_END_DATE"].isna() if has_end else pd.Series(True, index=df_works.index))
        )
        flagged = df_works[mask]

        findings = []
        for _, row in flagged.iterrows():
            sanc = safe_float(row.get("SANCTION_AMOUNT", 0.0))
            disb = safe_float(row.get("total_disbursed", 0.0))
            days = safe_float(row.get("days_since_sanction", 0.0))
            ratio = disb / sanc

            sev = float(np.clip(0.5 + (ratio - 0.85) * 2.0 + (days - 365) / 730.0 * 0.3, 0.5, 1.0))
            conf = float(np.clip(row.get("dqi_score", 0.8), 0.4, 1.0))

            work_id = str(row.get("WORK_ID") or row.get("WORK_RECOMMENDATION_DTL_ID"))
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])

            f = Finding(
                finding_id=f"FIND-D9-{rec_id}",
                work_id=work_id,
                work_rec_id=rec_id,
                detector_code=self.code,
                detector_name=self.name,
                category=self.category,
                severity=sev,
                confidence=conf,
                evidence={
                    "sanction_amount": sanc,
                    "total_disbursed": disb,
                    "disbursement_ratio": round(ratio, 3),
                    "days_since_sanction": days,
                    "completion_status": "Incomplete (No Actual End Date)",
                },
                explanation=(
                    f"Work has drawn ₹{disb:,.0f} ({ratio:.1%} of budget) over {int(days)} days since sanction, "
                    "yet lacks physical completion certification. Strong indicator of phantom progress or asset abandonment."
                ),
                next_review_action=(
                    "Dispatch District Quality Monitor (DQM) or Executive Magistrate for geo-tagged visual site inspection "
                    "and impound contractor final bill pending handover certificate."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=sanc,
            )
            findings.append(f)

        return findings
