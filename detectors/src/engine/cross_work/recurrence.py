"""
Entity Recurrence Anomaly Engine.

Tracks repeated appearances of the same Implementing Agencies or Vendors
across multiple independent anomaly findings using Empirical Bayes / Beta-Binomial
statistical exceedance testing to eliminate exposure/portfolio-size volume bias.
"""

from collections import defaultdict
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats

from src.engine.detectors.base import AnomalyCategory, Finding


class EntityRecurrenceDetector:
    """
    Surfaces systemic compliance or financial risk when entities recur across anomaly types
    at rates statistically exceeding their peer baseline expectation.

    Formulation:
    1. Exposure (N): Total portfolio size per agency/vendor.
    2. Numerator (k): Distinct anomalous works linked to the entity.
    3. Baseline (p0): Leave-one-out peer baseline failure rate.
    4. Empirical Bayes: Fits Beta(alpha, beta) prior via method of moments.
    5. Shrunk Rate: p_tilde = (k + alpha) / (N + alpha + beta).
    6. Exceedance Z: Z = (p_tilde - p0) / sqrt(p0 * (1 - p0) / N).
    7. Significance: Z >= 1.645 (p < 0.05, one-tailed) with FDR q-value correction.
    """

    def __init__(self, min_anomalies: int = 3, min_exposure: int = 3, significance_threshold: float = 1.645):
        self.code = "REC-D15"
        self.name = "Systemic Entity Anomaly Recurrence"
        self.category = AnomalyCategory.AGENCY
        self.min_anomalies = min_anomalies
        self.min_exposure = min_exposure
        self.significance_threshold = significance_threshold

    def _fit_prior(
        self,
        entity_portfolio: Dict[str, int],
        entity_anom_rec_ids: Dict[str, set],
    ) -> tuple[float, float, float, int, int]:
        total_k = sum(len(ids) for ids in entity_anom_rec_ids.values())
        total_N = sum(entity_portfolio.values())

        if total_N > 0 and total_k > 0:
            p0 = float(np.clip(total_k / total_N, 0.05, 0.95))
        else:
            p0 = 0.30

        qualifying_rates = [
            len(entity_anom_rec_ids.get(e, set())) / N for e, N in entity_portfolio.items() if N >= self.min_exposure
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

        return p0, alpha, beta, total_N, total_k

    def _evaluate_entities(
        self,
        entity_type: str,
        entity_findings: Dict[str, List[Finding]],
        entity_anom_rec_ids: Dict[str, set],
        entity_portfolio: Dict[str, int],
        work_dict: Dict[str, Any],
        p0: float,
        alpha: float,
        beta: float,
        total_N: int,
        total_k: int,
    ) -> List[Finding]:
        findings: List[Finding] = []
        is_vendor = entity_type == "VENDOR"
        category = AnomalyCategory.FINANCIAL if is_vendor else self.category
        display_type = "Vendor / Contractor" if is_vendor else "Implementing Agency"
        prefix = "VND" if is_vendor else "IA"

        candidate_data = []
        for entity, f_list in entity_findings.items():
            N = entity_portfolio.get(entity, 0)
            if N < self.min_exposure:
                continue

            anom_ids = entity_anom_rec_ids.get(entity, set())
            k = len(anom_ids)
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
                pval = float(stats.binomtest(k, N, p0_entity, alternative="greater").pvalue)
            except Exception:
                pval = 1.0 if z_score <= 0 else 0.01

            candidate_data.append({
                "entity": entity,
                "f_list": f_list,
                "anom_ids": anom_ids,
                "k": k,
                "N": N,
                "p0_entity": p0_entity,
                "shrunk_p": shrunk_p,
                "post_sd": post_sd,
                "z_score": z_score,
                "prob_exceed": prob_exceed,
                "pval": pval,
            })

        if not candidate_data:
            return findings

        # Benjamini-Hochberg False Discovery Rate (FDR) q-value calibration
        m = len(candidate_data)
        sorted_indices = sorted(range(m), key=lambda idx: candidate_data[idx]["pval"])
        q_values = [1.0] * m
        min_q = 1.0
        for rank_rev, idx in enumerate(reversed(sorted_indices), start=1):
            rank = m - rank_rev + 1
            raw_q = candidate_data[idx]["pval"] * m / rank
            min_q = min(min_q, raw_q)
            q_values[idx] = min(1.0, min_q)

        for idx, item in enumerate(candidate_data):
            entity = item["entity"]
            f_list = item["f_list"]
            anom_ids = item["anom_ids"]
            k = item["k"]
            N = item["N"]
            p0_entity = item["p0_entity"]
            shrunk_p = item["shrunk_p"]
            post_sd = item["post_sd"]
            z_score = item["z_score"]
            prob_exceed = item["prob_exceed"]
            pval = item["pval"]
            qval = q_values[idx]

            is_significant = (
                (qval <= 0.15 and z_score >= self.significance_threshold)
                or (prob_exceed >= 0.95 and z_score >= 1.0)
                or (pval <= 0.05 and z_score >= 1.5)
                or (k == N >= self.min_anomalies and N <= 5)
            )

            if is_significant:
                codes = sorted(list({f.detector_code for f in f_list}))
                excess_ratio = max(0.0, (shrunk_p - p0_entity) / max(1.0 - p0_entity, 0.05))
                severity = float(np.clip(0.50 + 0.50 * excess_ratio, 0.50, 1.0))
                exposure_factor = 1.0 - np.exp(-N / 20.0)
                confidence = float(np.clip(0.50 + 0.40 * exposure_factor + 0.10 * min(prob_exceed, 1.0), 0.50, 0.98))

                # Build findings for each of the k distinct anomalous works
                for rec_id in sorted(list(anom_ids)):
                    w = work_dict.get(rec_id)
                    work_id = str(w.get("WORK_ID") or rec_id) if w is not None else rec_id
                    state_name = w.get("STATE_NAME") if w is not None else None
                    ida_name = w.get("IDA_NAME") if w is not None else None
                    sanction_amt = float(w.get("SANCTION_AMOUNT", 0.0)) if w is not None else 0.0

                    f = Finding(
                        finding_id=f"FIND-D15-{prefix}-{rec_id}",
                        work_id=work_id,
                        work_rec_id=rec_id,
                        detector_code=self.code,
                        detector_name=f"Systemic {display_type} Recurrence",
                        category=category,
                        severity=round(severity, 3),
                        confidence=round(confidence, 3),
                        evidence={
                            "entity_type": "VENDOR" if is_vendor else "IMPLEMENTING_AGENCY",
                            "entity_name": entity,
                            "flagged_works_count": int(k),
                            "total_portfolio_works": int(N),
                            "raw_failure_rate": round(float(k / N), 4),
                            "shrunk_failure_rate": round(float(shrunk_p), 4),
                            "peer_baseline_rate": round(float(p0_entity), 4),
                            "posterior_std": round(float(post_sd), 4),
                            "posterior_exceedance_prob": round(float(prob_exceed), 4),
                            "z_score": round(float(z_score), 3),
                            "p_value": round(float(pval), 5),
                            "fdr_q_value": round(float(qval), 5),
                            "contributing_anomaly_types": codes,
                        },
                        explanation=(
                            f"{display_type} '{entity}' exhibits systemic anomaly recurrence: {k} of {N} works flagged "
                            f"(raw rate: {k / N:.1%}, peer baseline: {p0_entity:.1%}, shrunk rate: {shrunk_p:.1%}, z-score: +{z_score:.2f}, p={pval:.4f}). "
                            f"Demonstrates statistically significant irregularity recurrence across {len(codes)} anomaly categories ({', '.join(codes)})."
                        ),
                        next_review_action=(
                            f"Initiate institutional performance review for {display_type} '{entity}'. "
                            f"Audit project allocation concentration and inspect whether systemic capacity deficit accounts for {k} flagged works."
                            if not is_vendor
                            else f"Conduct comprehensive vendor audit for contractor '{entity}'. "
                            f"Inspect procurement integrity and deliverables across {k} flagged works."
                        ),
                        state_name=state_name,
                        ida_name=ida_name,
                        sanction_amount=sanction_amt,
                    )
                    findings.append(f)

        return findings

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

        # 3. Fit Empirical Bayes Prior and Evaluate Implementing Agencies
        p0_ia, alpha_ia, beta_ia, total_N_ia, total_k_ia = self._fit_prior(ia_portfolio, ia_anom_rec_ids)
        ia_findings_list = self._evaluate_entities(
            entity_type="IMPLEMENTING_AGENCY",
            entity_findings=ia_findings,
            entity_anom_rec_ids=ia_anom_rec_ids,
            entity_portfolio=ia_portfolio,
            work_dict=work_dict,
            p0=p0_ia,
            alpha=alpha_ia,
            beta=beta_ia,
            total_N=total_N_ia,
            total_k=total_k_ia,
        )

        # 4. Fit Empirical Bayes Prior and Evaluate Vendors
        p0_v, alpha_v, beta_v, total_N_v, total_k_v = self._fit_prior(v_portfolio, v_anom_rec_ids)
        v_findings_list = self._evaluate_entities(
            entity_type="VENDOR",
            entity_findings=v_findings,
            entity_anom_rec_ids=v_anom_rec_ids,
            entity_portfolio=v_portfolio,
            work_dict=work_dict,
            p0=p0_v,
            alpha=alpha_v,
            beta=beta_v,
            total_N=total_N_v,
            total_k=total_k_v,
        )

        return ia_findings_list + v_findings_list
