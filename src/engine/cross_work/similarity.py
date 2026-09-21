"""
Similarity and Duplicate Work Detection Engine.

Detects candidate duplicate or highly similar works within geographic and category blocks
using TF-IDF n-gram vectorization and financial proximity windows.
"""

from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.config import NETWORK
from src.engine.detectors.base import BaseDetector, Finding, AnomalyCategory


class DuplicateWorkDetector(BaseDetector):
    """Detects candidate duplicate works sharing high textual, spatial, and financial similarity."""

    def __init__(
        self,
        similarity_threshold: float = NETWORK.SIMILARITY_DUPLICATE_THRESHOLD,
        cost_window_ratio: float = NETWORK.SIMILARITY_COST_WINDOW_RATIO
    ):
        super().__init__(
            code="SIM-D12",
            name="Potentially Duplicate Work",
            category=AnomalyCategory.NETWORK_SIMILARITY
        )
        self.similarity_threshold = similarity_threshold
        self.cost_window_ratio = cost_window_ratio

    def detect(self, df_works: pd.DataFrame, baseline_engine: Optional[object] = None) -> List[Finding]:
        if "WORK_DESCRIPTION" not in df_works.columns or "SANCTION_AMOUNT" not in df_works.columns:
            return []

        valid = df_works[
            df_works["WORK_DESCRIPTION"].notna() &
            (df_works["WORK_DESCRIPTION"].astype(str).str.len() > 10) &
            (pd.to_numeric(df_works["SANCTION_AMOUNT"], errors="coerce") > 0)
        ].copy()

        if len(valid) < 2:
            return []

        findings: List[Finding] = []
        # Candidate blocking by State and Category to keep comparison tractable
        grp = valid.groupby(["STATE_NAME", "WORK_CATEGORY"])

        for (state, cat), sub in grp:
            if len(sub) < 2 or len(sub) > 500:
                # Skip trivial or excessively large single blocks for pair-wise matrix
                if len(sub) > 500:
                    sub = sub.head(500)
                else:
                    continue

            docs = sub["WORK_DESCRIPTION"].tolist()
            try:
                tfidf = TfidfVectorizer(ngram_range=(1, 3), max_features=1000)
                mat = tfidf.fit_transform(docs)
                sim_matrix = cosine_similarity(mat)
            except Exception:
                continue

            sub_records = sub.to_dict("records")
            n = len(sub_records)

            for i in range(n):
                for j in range(i + 1, n):
                    sim = float(sim_matrix[i, j])
                    if sim < self.similarity_threshold:
                        continue

                    w1, w2 = sub_records[i], sub_records[j]
                    # Check cost proximity
                    c1 = float(w1["SANCTION_AMOUNT"])
                    c2 = float(w2["SANCTION_AMOUNT"])
                    diff = abs(c1 - c2)
                    max_c = max(c1, c2)
                    if max_c > 0 and (diff / max_c) <= self.cost_window_ratio:
                        # Spatial proximity bonus if same district/IDA
                        same_district = (w1.get("IDA_NAME") == w2.get("IDA_NAME"))
                        composite_score = sim * (1.1 if same_district else 1.0)
                        sev = float(np.clip((composite_score - 0.75) * 2.5, 0.4, 0.95))
                        conf = 0.85 if same_district else 0.70

                        rec_id1 = str(w1["WORK_RECOMMENDATION_DTL_ID"])
                        rec_id2 = str(w2["WORK_RECOMMENDATION_DTL_ID"])
                        work_id1 = str(w1.get("WORK_ID") or rec_id1)

                        f = Finding(
                            finding_id=f"FIND-D12-{rec_id1}-{rec_id2}",
                            work_id=work_id1,
                            work_rec_id=rec_id1,
                            detector_code=self.code,
                            detector_name=self.name,
                            category=self.category,
                            severity=sev,
                            confidence=conf,
                            evidence={
                                "matched_work_rec_id": rec_id2,
                                "matched_work_id": str(w2.get("WORK_ID") or rec_id2),
                                "text_similarity": round(sim, 3),
                                "work_1_desc": w1["WORK_DESCRIPTION"][:100],
                                "work_2_desc": w2["WORK_DESCRIPTION"][:100],
                                "work_1_cost": c1,
                                "work_2_cost": c2,
                                "same_district": same_district,
                                "district_1": w1.get("IDA_NAME"),
                                "district_2": w2.get("IDA_NAME")
                            },
                            explanation=(
                                f"Work shares {sim:.1%} text description similarity and matching cost (₹{c1:,.0f} vs ₹{c2:,.0f}) "
                                f"with Work {rec_id2} in {state}. Candidate for duplicate billing or repeated scope."
                            ),
                            next_review_action=(
                                "Conduct field verification of GPS coordinates and photographic completion evidence to confirm "
                                "the two records represent distinct physical assets and not duplicate funding of one structure."
                            ),
                            state_name=state,
                            ida_name=w1.get("IDA_NAME"),
                            sanction_amount=c1
                        )
                        findings.append(f)
                        if len(findings) >= 500:
                            return findings

        return findings
