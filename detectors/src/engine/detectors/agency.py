"""
Implementing Agency Baseline and Workload Anomaly Detectors.

Evaluates Implementing Agency (IA) operational capacity, backlog concentration,
and multi-district execution bottlenecks.
"""

from typing import List, Optional

import numpy as np
import pandas as pd

from src.engine.detectors.base import AnomalyCategory, BaseDetector, Finding, safe_float


class IAOverloadDetector(BaseDetector):
    """Detects Implementing Agencies with excessive backlogs of delayed unfinished works."""

    def __init__(self, min_delayed_works: int = 10, min_total_expenditure: float = 5000000.0):
        super().__init__(code="AGY-D11", name="Implementing Agency Capacity Overload", category=AnomalyCategory.AGENCY)
        self.min_delayed_works = min_delayed_works
        self.min_total_expenditure = min_total_expenditure

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        if "ia_name" not in df_works.columns:
            return []

        disallowed = {"", "N/A", "NA", "NAN", "NONE", "NULL", "NOT APPLICABLE", "OTHER", "UNKNOWN"}
        valid_ias = df_works[
            df_works["ia_name"].notna()
            & (~df_works["ia_name"].astype(str).str.strip().str.upper().isin(disallowed))
        ].copy()
        if valid_ias.empty:
            return []

        # Find delayed unfinished works per IA
        is_delayed_ongoing = (valid_ias["ACTUAL_END_DATE"].isna()) & (valid_ias["days_since_sanction"] > 365)
        valid_ias["is_delayed_ongoing"] = is_delayed_ongoing

        grp = valid_ias.groupby("ia_name")
        ia_stats = grp.agg(
            total_works=("WORK_RECOMMENDATION_DTL_ID", "count"),
            delayed_works=("is_delayed_ongoing", "sum"),
            total_disbursed=("total_disbursed", "sum"),
            districts_count=("IDA_NAME", "nunique"),
        ).reset_index()

        overloaded_ias = ia_stats[
            (ia_stats["delayed_works"] >= self.min_delayed_works)
            & (ia_stats["total_disbursed"] >= self.min_total_expenditure)
        ]

        findings = []
        if overloaded_ias.empty:
            return findings

        # Map back to delayed works of these overloaded IAs
        overloaded_set = set(overloaded_ias["ia_name"])
        target_works = valid_ias[valid_ias["ia_name"].isin(overloaded_set) & is_delayed_ongoing]

        for _, row in target_works.iterrows():
            ia_name = str(row["ia_name"])
            ia_info = overloaded_ias[overloaded_ias["ia_name"] == ia_name].iloc[0]

            delayed_cnt = int(ia_info["delayed_works"])
            tot_cnt = int(ia_info["total_works"])
            dist_cnt = int(ia_info["districts_count"])
            tot_disb = float(ia_info["total_disbursed"])

            sev = float(np.clip(0.4 + (delayed_cnt / 50.0) * 0.6, 0.4, 1.0))
            conf = 0.85

            work_id = str(row.get("WORK_ID") or row.get("WORK_RECOMMENDATION_DTL_ID"))
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])

            f = Finding(
                finding_id=f"FIND-D11-{rec_id}",
                work_id=work_id,
                work_rec_id=rec_id,
                detector_code=self.code,
                detector_name=self.name,
                category=self.category,
                severity=sev,
                confidence=conf,
                evidence={
                    "ia_name": ia_name,
                    "agency_delayed_works": delayed_cnt,
                    "agency_total_works": tot_cnt,
                    "districts_operating_in": dist_cnt,
                    "agency_total_disbursed": tot_disb,
                },
                explanation=(
                    f"Executing Agency '{ia_name}' is burdened with {delayed_cnt} unfinished works exceeding 1 year "
                    f"across {dist_cnt} district(s), with ₹{tot_disb:,.0f} committed funds. Creates severe structural delivery risk."
                ),
                next_review_action=(
                    "Enforce administrative moratorium on assigning new MPLADS works to this agency and review "
                    "re-allocation of delayed works to alternative state engineering divisions."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=safe_float(row.get("SANCTION_AMOUNT", 0.0)),
            )
            findings.append(f)

        return findings
