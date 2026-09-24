"""
MPLADS Baseline Engine.

Calculates statutory policy baselines, dynamic statistical peer groups,
and historical moving baselines for works, costs, and lifecycles.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.config import STATISTICS


@dataclass
class PeerBaseline:
    """Holds computed statistical baseline for a peer cohort."""

    cohort_key: Tuple[str, ...]
    sample_size: int
    cost_median: float
    cost_iqr: float
    cost_mean: float
    cost_std: float
    days_sanc_median: float
    days_comp_median: float


class BaselineEngine:
    """Computes and queries policy, peer-group, and historical baselines."""

    def __init__(self, min_sample_size: int = STATISTICS.MIN_PEER_GROUP_SIZE):
        self.min_sample_size = min_sample_size
        self.peer_baselines: Dict[Tuple[str, str], PeerBaseline] = {}
        self.category_baselines: Dict[str, PeerBaseline] = {}
        self.global_baseline: Optional[PeerBaseline] = None

    def fit(self, df_works: pd.DataFrame) -> "BaselineEngine":
        """Fits peer group distributions across (STATE_NAME, WORK_CATEGORY)."""
        valid_works = df_works[df_works["SANCTION_AMOUNT"] > 0].copy()

        # 1. State x Category cohorts
        grp = valid_works.groupby(["STATE_NAME", "WORK_CATEGORY"])
        for (state, cat), sub in grp:
            if len(sub) >= self.min_sample_size:
                q25 = sub["SANCTION_AMOUNT"].quantile(0.25)
                q75 = sub["SANCTION_AMOUNT"].quantile(0.75)
                iqr = max(q75 - q25, 1.0)
                self.peer_baselines[(str(state), str(cat))] = PeerBaseline(
                    cohort_key=(str(state), str(cat)),
                    sample_size=len(sub),
                    cost_median=float(sub["SANCTION_AMOUNT"].median()),
                    cost_iqr=float(iqr),
                    cost_mean=float(sub["SANCTION_AMOUNT"].mean()),
                    cost_std=float(sub["SANCTION_AMOUNT"].std(ddof=1) if len(sub) > 1 else 0.0),
                    days_sanc_median=float(
                        sub["days_rec_to_sanction"].dropna().median()
                        if "days_rec_to_sanction" in sub.columns and not sub["days_rec_to_sanction"].dropna().empty
                        else 45.0
                    ),
                    days_comp_median=float(
                        sub["days_sanction_to_completion"].dropna().median()
                        if "days_sanction_to_completion" in sub.columns
                        and not sub["days_sanction_to_completion"].dropna().empty
                        else 365.0
                    ),
                )

        # 2. Category fallback cohorts
        cat_grp = valid_works.groupby("WORK_CATEGORY")
        for cat, sub in cat_grp:
            if len(sub) >= self.min_sample_size:
                q25 = sub["SANCTION_AMOUNT"].quantile(0.25)
                q75 = sub["SANCTION_AMOUNT"].quantile(0.75)
                iqr = max(q75 - q25, 1.0)
                self.category_baselines[str(cat)] = PeerBaseline(
                    cohort_key=(str(cat),),
                    sample_size=len(sub),
                    cost_median=float(sub["SANCTION_AMOUNT"].median()),
                    cost_iqr=float(iqr),
                    cost_mean=float(sub["SANCTION_AMOUNT"].mean()),
                    cost_std=float(sub["SANCTION_AMOUNT"].std(ddof=1) if len(sub) > 1 else 0.0),
                    days_sanc_median=float(
                        sub["days_rec_to_sanction"].dropna().median()
                        if "days_rec_to_sanction" in sub.columns and not sub["days_rec_to_sanction"].dropna().empty
                        else 45.0
                    ),
                    days_comp_median=float(
                        sub["days_sanction_to_completion"].dropna().median()
                        if "days_sanction_to_completion" in sub.columns
                        and not sub["days_sanction_to_completion"].dropna().empty
                        else 365.0
                    ),
                )

        # 3. Global baseline fallback
        if len(valid_works) > 0:
            q25 = valid_works["SANCTION_AMOUNT"].quantile(0.25)
            q75 = valid_works["SANCTION_AMOUNT"].quantile(0.75)
            self.global_baseline = PeerBaseline(
                cohort_key=("GLOBAL",),
                sample_size=len(valid_works),
                cost_median=float(valid_works["SANCTION_AMOUNT"].median()),
                cost_iqr=float(max(q75 - q25, 1.0)),
                cost_mean=float(valid_works["SANCTION_AMOUNT"].mean()),
                cost_std=float(valid_works["SANCTION_AMOUNT"].std(ddof=1)),
                days_sanc_median=float(
                    valid_works["days_rec_to_sanction"].dropna().median()
                    if "days_rec_to_sanction" in valid_works.columns
                    and not valid_works["days_rec_to_sanction"].dropna().empty
                    else 45.0
                ),
                days_comp_median=float(
                    valid_works["days_sanction_to_completion"].dropna().median()
                    if "days_sanction_to_completion" in valid_works.columns
                    and not valid_works["days_sanction_to_completion"].dropna().empty
                    else 365.0
                ),
            )

        return self

    def get_peer_baseline(self, state: Optional[str], category: Optional[str]) -> Tuple[Optional[PeerBaseline], float]:
        """
        Retrieves baseline matching State x Category with hierarchy fallback.
        Returns: (PeerBaseline, confidence_factor [0.0 - 1.0])
        """
        key = (str(state), str(category))
        if key in self.peer_baselines:
            base = self.peer_baselines[key]
            # Confidence scales logarithmically with sample size, capped at 1.0
            conf = min(1.0, float(np.log10(max(base.sample_size, 10)) / 3.0))
            return base, conf

        if category and str(category) in self.category_baselines:
            base = self.category_baselines[str(category)]
            conf = min(0.75, float(np.log10(max(base.sample_size, 10)) / 4.0))
            return base, conf

        return self.global_baseline, 0.40
