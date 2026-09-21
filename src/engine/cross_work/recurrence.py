"""
Entity Recurrence Anomaly Engine.

Tracks repeated appearances of the same Implementing Agencies or Vendors
across multiple independent anomaly findings using Empirical Bayes / Beta-Binomial
statistical exceedance testing to eliminate exposure/portfolio-size volume bias.
"""

from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy import stats
from src.engine.detectors.base import Finding, AnomalyCategory


class EntityRecurrenceDetector:
    """
    Surfaces systemic compliance or financial risk when entities recur across anomaly types
    at rates statistically exceeding their peer baseline expectation.
    """

    def __init__(
        self,
        min_anomalies: int = 3,
        min_exposure: int = 3,
        significance_threshold: float = 1.645
    ):
        self.code = "REC-D15"
        self.name = "Systemic Entity Anomaly Recurrence"
        self.category = AnomalyCategory.AGENCY
        self.min_anomalies = min_anomalies
        self.min_exposure = min_exposure
        self.significance_threshold = significance_threshold

    def detect(self, df_works: pd.DataFrame, prior_findings: List[Finding]) -> List[Finding]:
        if not prior_findings or df_works.empty:
            return []

        # Map findings to works
        rec_to_findings: Dict[str, List[Finding]] = defaultdict(list)
        for f in prior_findings:
            if f.work_rec_id:
                rec_to_findings[str(f.work_rec_id)].append(f)

        work_dict = {
            str(r["WORK_RECOMMENDATION_DTL_ID"]): r
            for _, r in df_works.iterrows()
            if pd.notna(r.get("WORK_RECOMMENDATION_DTL_ID"))
        }

        # 1. Measure portfolio size (exposure N) per IA and Vendor
        ia_portfolio: Dict[str, int] = defaultdict(int)
        v_portfolio: Dict[str, int] = defaultdict(int)

        for rec_id, r in work_dict.items():
            ia = r.get("ia_name")
            if ia and pd.notna(ia):
                ia_str = str(ia).strip()
                ia_portfolio[ia_str] += 1
            v = r.get("primary_vendor")
            if v and pd.notna(v):
                v_str = str(v).strip()
                v_portfolio[v_str] += 1

        # 2. Measure unique anomalous works (k) per IA and Vendor
        ia_findings: Dict[str, List[Finding]] = defaultdict(list)
        ia_anom_rec_ids: Dict[str, set] = defaultdict(set)
        v_findings: Dict[str, List[Finding]] = defaultdict(list)
        v_anom_rec_ids: Dict[str, set] = defaultdict(set)

        for rec_id, f_list in rec_to_findings.items():
            if rec_id in work_dict:
                w = work_dict[rec_id]
                ia = w.get("ia_name")
                if ia and pd.notna(ia):
                    ia_str = str(ia).strip()
                    ia_findings[ia_str].extend(f_list)
                    ia_anom_rec_ids[ia_str].add(rec_id)
                v = w.get("primary_vendor")
                if v and pd.notna(v):
                    v_str = str(v).strip()
                    v_findings[v_str].extend(f_list)
                    v_anom_rec_ids[v_str].add(rec_id)

        # 3. Fit Peer Baseline Anomaly Rate and Empirical Bayes Prior
        total_k = sum(len(ids) for ids in ia_anom_rec_ids.values())
        total_N = sum(ia_portfolio.values())
        
        if total_N > 0 and total_k > 0:
            p0 = float(np.clip(total_k / total_N, 0.05, 0.95))
        else:
            p0 = 0.30

        # Empirical Bayes Beta(alpha, beta) estimation across agencies with exposure >= min_exposure
        qualifying_rates = [
            len(ia_anom_rec_ids.get(ia, set())) / N
            for ia, N in ia_portfolio.items()
            if N >= self.min_exposure
        ]

        if len(qualifying_rates) >= 5:
            mean_rate = float(np.mean(qualifying_rates))
            var_rate = float(np.var(qualifying_rates, ddof=1))
            if 0 < var_rate < mean_rate * (1.0 - mean_rate):
                common = (mean_rate * (1.0 - mean_rate) / var_rate) - 1.0
                alpha = max(0.5, mean_rate * common)
                beta = max(0.5, (1.0 - mean_rate) * common)
            else:
                alpha, beta = 1.0, max(1.0, (1.0 - p0) / p0)
        else:
            alpha = 1.0
            beta = max(1.0, (1.0 - p0) / p0)

        recurrence_findings: List[Finding] = []

        # 4. Evaluate each Implementing Agency under Empirical Bayes Normalization
        for ia, f_list in ia_findings.items():
            N = ia_portfolio.get(ia, 0)
            if N < self.min_exposure:
                continue

            k = len(ia_anom_rec_ids.get(ia, set()))
            if k < self.min_anomalies:
                continue

            peer_N = total_N - N
            peer_k = total_k - k
            if peer_N >= self.min_exposure and peer_k > 0:
                p0_entity = float(np.clip(peer_k / peer_N, 0.05, 0.95))
            else:
                p0_entity = p0 if total_N > N else 0.30

            # Shrunk failure rate under Beta-Binomial conjugate model
            shrunk_p = float((k + alpha) / (N + alpha + beta))
            # Exact model-consistent posterior standard deviation
            post_sd = float(np.sqrt((shrunk_p * (1.0 - shrunk_p)) / (N + alpha + beta + 1)))
            z_score = float((shrunk_p - p0_entity) / post_sd) if post_sd > 0 else 0.0

            # Exact posterior exceedance probability P(theta > p0 | k, N)
            try:
                prob_exceed = float(stats.beta.sf(p0_entity, alpha + k, beta + N - k))
            except Exception:
                prob_exceed = 0.50

            try:
                pval = float(stats.binomtest(k, N, p0_entity, alternative='greater').pvalue)
            except Exception:
                pval = 1.0 if z_score <= 0 else 0.01

            is_significant = (z_score >= self.significance_threshold) or (prob_exceed >= 0.95) or (pval <= 0.05) or (k == N >= self.min_anomalies and N <= 5)

            if is_significant:
                codes = sorted(list({f.detector_code for f in f_list}))
                sample_finding = f_list[0]
                rec_id = str(sample_finding.work_rec_id)
                work_id = str(sample_finding.work_id)

                excess_ratio = max(0.0, (shrunk_p - p0_entity) / max(1.0 - p0_entity, 0.05))
                severity = float(np.clip(0.50 + 0.50 * excess_ratio, 0.50, 1.0))
                exposure_factor = 1.0 - np.exp(-N / 20.0)
                confidence = float(np.clip(0.50 + 0.40 * exposure_factor + 0.10 * min(prob_exceed, 1.0), 0.50, 0.98))

                f = Finding(
                    finding_id=f"FIND-D15-IA-{abs(hash(ia)) % 100000}",
                    work_id=work_id,
                    work_rec_id=rec_id,
                    detector_code=self.code,
                    detector_name=self.name,
                    category=self.category,
                    severity=round(severity, 3),
                    confidence=round(confidence, 3),
                    evidence={
                        "entity_type": "IMPLEMENTING_AGENCY",
                        "entity_name": ia,
                        "flagged_works_count": int(k),
                        "total_portfolio_works": int(N),
                        "raw_failure_rate": round(float(k / N), 4),
                        "shrunk_failure_rate": round(float(shrunk_p), 4),
                        "peer_baseline_rate": round(float(p0_entity), 4),
                        "posterior_std": round(float(post_sd), 4),
                        "posterior_exceedance_prob": round(float(prob_exceed), 4),
                        "z_score": round(float(z_score), 3),
                        "p_value": round(float(pval), 5),
                        "contributing_anomaly_types": codes
                    },
                    explanation=(
                        f"Implementing Agency '{ia}' exhibits systemic anomaly recurrence: {k} of {N} works flagged "
                        f"(raw rate: {k/N:.1%}, peer baseline: {p0_entity:.1%}, shrunk rate: {shrunk_p:.1%}, z-score: +{z_score:.2f}, p={pval:.4f}). "
                        f"Demonstrates statistically significant irregularity recurrence across {len(codes)} anomaly categories ({', '.join(codes)})."
                    ),
                    next_review_action=(
                        f"Initiate state nodal institutional performance review for Implementing Agency '{ia}'. "
                        f"Audit project allocation concentration and inspect whether systemic capacity deficit accounts for {k} flagged works."
                    ),
                    state_name=sample_finding.state_name,
                    ida_name=sample_finding.ida_name,
                    sanction_amount=sample_finding.sanction_amount
                )
                recurrence_findings.append(f)

        return recurrence_findings
