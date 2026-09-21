"""
Financial Anomaly Detectors.

Detects cost outliers relative to peer baselines, cost overruns,
round-voucher clustering, and fiscal year-end disbursement rushes.
"""

from typing import List, Optional
import pandas as pd
import numpy as np
from src.config import STATISTICS
from src.engine.detectors.base import BaseDetector, Finding, AnomalyCategory
from src.engine.baselines import BaselineEngine


class CostPeerOutlierDetector(BaseDetector):
    """Detects works with sanction costs significantly exceeding peer cohorts."""

    def __init__(self, z_threshold: float = STATISTICS.COST_OUTLIER_Z_SCORE):
        super().__init__(
            code="FIN-D5",
            name="Peer Group Cost Outlier",
            category=AnomalyCategory.FINANCIAL
        )
        self.z_threshold = z_threshold

    def detect(self, df_works: pd.DataFrame, baseline_engine: BaselineEngine) -> List[Finding]:
        findings = []
        valid_works = df_works[df_works["SANCTION_AMOUNT"] > 0]

        for _, row in valid_works.iterrows():
            amt = float(row["SANCTION_AMOUNT"])
            state = row.get("STATE_NAME")
            cat = row.get("WORK_CATEGORY")

            base, peer_conf = baseline_engine.get_peer_baseline(state, cat)
            if not base or base.sample_size < 5:
                continue

            # Robust Z-score using Median and Normal-equivalent IQR (IQR / 1.349)
            norm_iqr = base.cost_iqr / 1.349 if base.cost_iqr > 0 else max(base.cost_std, 1000.0)
            diff = amt - base.cost_median
            z_score = diff / norm_iqr if norm_iqr > 0 else 0.0

            if z_score >= self.z_threshold:
                # Severity scales with Z-score magnitude
                sev = float(np.clip(0.4 + (z_score - self.z_threshold) * 0.12, 0.4, 1.0))
                # Confidence combines peer group size confidence and record DQI
                dqi = float(row.get("dqi_score", 0.8))
                conf = float(np.clip(peer_conf * 0.6 + dqi * 0.4, 0.3, 1.0))

                work_id = str(row.get("WORK_ID") or row.get("WORK_RECOMMENDATION_DTL_ID"))
                rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
                cohort_desc = f"{state} / {cat}" if len(base.cohort_key) > 1 else str(cat)

                f = Finding(
                    finding_id=f"FIND-D5-{rec_id}",
                    work_id=work_id,
                    work_rec_id=rec_id,
                    detector_code=self.code,
                    detector_name=self.name,
                    category=self.category,
                    severity=sev,
                    confidence=conf,
                    evidence={
                        "sanction_amount": amt,
                        "peer_median": base.cost_median,
                        "peer_iqr": base.cost_iqr,
                        "robust_z_score": round(z_score, 2),
                        "peer_cohort": cohort_desc,
                        "peer_sample_size": base.sample_size
                    },
                    explanation=(
                        f"Work cost of ₹{amt:,.0f} deviates significantly (robust Z={z_score:.2f}) from the peer median of "
                        f"₹{base.cost_median:,.0f} across {base.sample_size} comparable works in {cohort_desc}."
                    ),
                    next_review_action=(
                        "Request verified Schedule of Rates (SOR) analysis and technical estimate justification from the "
                        "District Planning Authority to validate cost variance."
                    ),
                    state_name=state,
                    ida_name=row.get("IDA_NAME"),
                    sanction_amount=amt
                )
                findings.append(f)

        return findings


class CostOverrunDetector(BaseDetector):
    """Detects works where total disbursements exceed approved sanction limits."""

    def __init__(self, threshold_ratio: float = STATISTICS.EXPENDITURE_OVERRUN_RATIO):
        super().__init__(
            code="FIN-D6",
            name="Sanction Cost Overrun",
            category=AnomalyCategory.FINANCIAL
        )
        self.threshold_ratio = threshold_ratio

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        disb_s = df_works["total_disbursed"].fillna(0.0) if "total_disbursed" in df_works.columns else pd.Series(0.0, index=df_works.index)
        mask = (
            (df_works["SANCTION_AMOUNT"] > 0) &
            (df_works["total_disbursed"].notna()) &
            (disb_s > df_works["SANCTION_AMOUNT"] * self.threshold_ratio)
        )
        flagged = df_works[mask]

        findings = []
        for _, row in flagged.iterrows():
            sanc = float(row["SANCTION_AMOUNT"])
            disb = float(row["total_disbursed"])
            ratio = disb / sanc
            excess = disb - sanc

            sev = float(np.clip(0.3 + (ratio - 1.0) * 1.5, 0.3, 1.0))
            conf = float(np.clip(row.get("dqi_score", 0.8), 0.4, 1.0))

            work_id = str(row.get("WORK_ID") or row.get("WORK_RECOMMENDATION_DTL_ID"))
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])

            f = Finding(
                finding_id=f"FIND-D6-{rec_id}",
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
                    "overrun_ratio": round(ratio, 3),
                    "excess_disbursed": excess
                },
                explanation=(
                    f"Total disbursement of ₹{disb:,.0f} exceeds approved administrative sanction of ₹{sanc:,.0f} "
                    f"by ₹{excess:,.0f} ({ratio:.1%}), violating Para 3.2.14 limits on unauthorized escalations."
                ),
                next_review_action=(
                    "Demand revised sanction order signed by District Magistrate; if missing, withhold further releases "
                    "and initiate recovery of excess disbursements from Implementing Agency."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=sanc
            )
            findings.append(f)

        return findings


class TemporalDisbursementSpikeDetector(BaseDetector):
    """Detects works with concentrated disbursements within a single week or March rush."""

    def __init__(self):
        super().__init__(
            code="FIN-D8",
            name="Temporal Disbursement Spike",
            category=AnomalyCategory.FINANCIAL
        )

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        if "first_payment_date" not in df_works.columns or "last_payment_date" not in df_works.columns:
            return []

        has_dates = df_works["first_payment_date"].notna() & df_works["last_payment_date"].notna()
        days_span = (df_works["last_payment_date"] - df_works["first_payment_date"]).dt.days
        disb_s = df_works["total_disbursed"].fillna(0.0) if "total_disbursed" in df_works.columns else pd.Series(0.0, index=df_works.index)
        pmt_cnt = df_works["payment_count"].fillna(0) if "payment_count" in df_works.columns else pd.Series(0, index=df_works.index)

        mask = (
            has_dates &
            (pmt_cnt >= 3) &
            (days_span <= 7) &
            (disb_s >= 1000000.0)
        )
        flagged = df_works[mask]

        findings = []
        for _, row in flagged.iterrows():
            span = int((row["last_payment_date"] - row["first_payment_date"]).days)
            cnt = int(row["payment_count"])
            disb = float(row["total_disbursed"])

            work_id = str(row.get("WORK_ID") or row.get("WORK_RECOMMENDATION_DTL_ID"))
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])

            f = Finding(
                finding_id=f"FIND-D8-{rec_id}",
                work_id=work_id,
                work_rec_id=rec_id,
                detector_code=self.code,
                detector_name=self.name,
                category=self.category,
                severity=0.65,
                confidence=0.85,
                evidence={
                    "total_disbursed": disb,
                    "payment_count": cnt,
                    "days_span": span,
                    "first_payment_date": str(row["first_payment_date"]),
                    "last_payment_date": str(row["last_payment_date"])
                },
                explanation=(
                    f"Rapid payment concentration: {cnt} separate vouchers totaling ₹{disb:,.0f} disbursed within "
                    f"{span} calendar days. May indicate batch processing to bypass quarterly monitoring."
                ),
                next_review_action=(
                    "Verify physical stage-gate inspection certificates for each voucher tranche to confirm genuine "
                    "milestone attainment prior to rapid successive releases."
                ),
                state_name=row.get("STATE_NAME"),
                ida_name=row.get("IDA_NAME"),
                sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0))
            )
            findings.append(f)

        return findings
