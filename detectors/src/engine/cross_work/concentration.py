"""
Entity Concentration and Monopolization Detection Engine.

Computes Herfindahl-Hirschman Index (HHI) and volume capture ratios for
Implementing Agencies and Contractors/Vendors across districts.
"""

from typing import List, Optional

import numpy as np
import pandas as pd

from src.config import NETWORK
from src.engine.detectors.base import AnomalyCategory, BaseDetector, Finding


class AgencyConcentrationDetector(BaseDetector):
    """Detects district-level implementing agency monopolization using HHI."""

    def __init__(
        self,
        hhi_threshold: float = NETWORK.HHI_HIGH_CONCENTRATION,
        share_threshold: float = NETWORK.TOP_ENTITY_SHARE_THRESHOLD,
    ):
        super().__init__(code="AGY-D13", name="District Agency Monopolization", category=AnomalyCategory.AGENCY)
        self.hhi_threshold = hhi_threshold
        self.share_threshold = share_threshold

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        valid = df_works[df_works["IDA_NAME"].notna() & df_works["ia_name"].notna()].copy()
        if valid.empty:
            return []

        findings: List[Finding] = []
        grp = valid.groupby("IDA_NAME")

        for district, sub in grp:
            if len(sub) < 15:  # Minimum works for market concentration measurement
                continue

            ia_counts = sub["ia_name"].value_counts()
            total_works = len(sub)
            shares = (ia_counts / total_works) * 100.0  # Percentage shares
            hhi = float((shares**2).sum())

            top_ia = ia_counts.index[0]
            top_share = float(shares.iloc[0] / 100.0)
            cr3 = float(shares.head(3).sum() / 100.0)

            if hhi >= self.hhi_threshold and top_share >= self.share_threshold:
                # Flag the works belonging to this dominant IA in this district
                dominant_works = sub[sub["ia_name"] == top_ia]
                is_single_agency = (len(ia_counts) == 1) or (top_share >= 0.80)
                statutory_note = (
                    " Note: High concentration observed. Reviewers should verify if local Panchayati Raj / State statutory guidelines "
                    "designate a single implementing agency (e.g. DRDA / Zila Parishad) for this jurisdiction."
                    if is_single_agency
                    else ""
                )
                # Prioritize top financial exposure works for the reviewer queue
                dominant_works_sorted = dominant_works.sort_values(by="SANCTION_AMOUNT", ascending=False) if "SANCTION_AMOUNT" in dominant_works.columns else dominant_works
                for _, row in dominant_works_sorted.head(5).iterrows():  # Top exposure works for reviewer queue
                    rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
                    work_id = str(row.get("WORK_ID") or rec_id)

                    sev = float(np.clip(0.4 + (top_share - 0.40) * 1.2, 0.4, 0.9))
                    conf = 0.85

                    f = Finding(
                        finding_id=f"FIND-D13-{rec_id}",
                        work_id=work_id,
                        work_rec_id=rec_id,
                        detector_code=self.code,
                        detector_name=self.name,
                        category=self.category,
                        severity=sev,
                        confidence=conf,
                        evidence={
                            "district": str(district),
                            "dominant_ia": top_ia,
                            "district_hhi": round(hhi, 1),
                            "agency_share_pct": round(top_share * 100, 1),
                            "cr1": round(top_share, 3),
                            "cr3": round(cr3, 3),
                            "agency_work_count": int(ia_counts.iloc[0]),
                            "district_total_works": total_works,
                            "statutory_single_agency_candidate": bool(is_single_agency),
                        },
                        explanation=(
                            f"Implementing Agency '{top_ia}' monopolizes {top_share:.1%} of works in District '{district}' "
                            f"(CR1: {top_share:.1%}, CR3: {cr3:.1%}, District HHI: {hhi:.0f}), exceeding competitive thresholds and creating institutional capture risk."
                            + statutory_note
                        ),
                        next_review_action=(
                            "Review district agency selection criteria; mandate open distribution of future project sanctions "
                            "across alternative state departments to avoid single-agency bottleneck."
                        ),
                        state_name=row.get("STATE_NAME"),
                        ida_name=str(district),
                        sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0)),
                    )
                    findings.append(f)

        return findings


class VendorConcentrationDetector(BaseDetector):
    """Detects vendor payment monopolization within district jurisdictions."""

    def __init__(self, share_threshold: float = 0.50, min_vendor_works: int = 5):
        super().__init__(
            code="VND-D14", name="Vendor Payment Monopolization", category=AnomalyCategory.NETWORK_SIMILARITY
        )
        self.share_threshold = share_threshold
        self.min_vendor_works = min_vendor_works

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        disb_s = (
            df_works["total_disbursed"].fillna(0.0)
            if "total_disbursed" in df_works.columns
            else pd.Series(0.0, index=df_works.index)
        )
        valid = df_works[df_works["IDA_NAME"].notna() & df_works["primary_vendor"].notna() & (disb_s > 0)].copy()

        if valid.empty:
            return []

        findings: List[Finding] = []
        grp = valid.groupby("IDA_NAME")

        for district, sub in grp:
            dist_total_disb = sub["total_disbursed"].sum()
            if dist_total_disb < 1000000.0 or len(sub) < 10:
                continue

            v_agg = (
                sub.groupby("primary_vendor")
                .agg(vendor_disb=("total_disbursed", "sum"), vendor_works=("WORK_RECOMMENDATION_DTL_ID", "count"))
                .reset_index()
            )

            v_agg["disb_share"] = v_agg["vendor_disb"] / dist_total_disb
            top_vendors = v_agg[
                (v_agg["disb_share"] >= self.share_threshold) & (v_agg["vendor_works"] >= self.min_vendor_works)
            ]

            for _, v_row in top_vendors.iterrows():
                v_name = str(v_row["primary_vendor"])
                v_share = float(v_row["disb_share"])
                v_works = int(v_row["vendor_works"])
                v_disb = float(v_row["vendor_disb"])

                # Prioritize top financial disbursements for the reviewer queue
                v_works_matched = sub[sub["primary_vendor"] == v_name]
                sample_works = v_works_matched.sort_values(by="total_disbursed", ascending=False).head(3)
                for _, row in sample_works.iterrows():
                    rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
                    work_id = str(row.get("WORK_ID") or rec_id)

                    sev = float(np.clip(0.5 + (v_share - 0.50) * 1.2, 0.5, 0.95))
                    conf = 0.90

                    f = Finding(
                        finding_id=f"FIND-D14-{rec_id}",
                        work_id=work_id,
                        work_rec_id=rec_id,
                        detector_code=self.code,
                        detector_name=self.name,
                        category=self.category,
                        severity=sev,
                        confidence=conf,
                        evidence={
                            "district": str(district),
                            "vendor_name": v_name,
                            "vendor_share_pct": round(v_share * 100, 1),
                            "vendor_total_disbursed": v_disb,
                            "vendor_work_count": v_works,
                            "district_total_disbursed": dist_total_disb,
                        },
                        explanation=(
                            f"Vendor '{v_name}' captures {v_share:.1%} (₹{v_disb:,.0f}) of all disbursed funds in District '{district}' "
                            f"across {v_works} works. Highly unusual procurement concentration indicating possible favored contractor."
                        ),
                        next_review_action=(
                            "Examine e-procurement tender logs for bid rigging, single-bidder awards, or non-competitive "
                            "tender splitting favoring this contractor."
                        ),
                        state_name=row.get("STATE_NAME"),
                        ida_name=str(district),
                        sanction_amount=float(row.get("SANCTION_AMOUNT", 0.0)),
                    )
                    findings.append(f)

        return findings
