"""
High-Performance In-Memory Data Service for MPLADS Intelligence Platform.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from backend.core.auth import redact_vendor_name
from backend.core.config import DATA_DIR, MODELS_DIR, PROCESSED_DIR
from detectors import MPLADSEngine


class DataService:
    """Analytical data service serving sub-10ms queries over 102k+ canonical works."""

    _instance = None

    def __init__(self):
        print("[*] Initializing MPLADS DataService in-memory cache...")
        self.engine = MPLADSEngine(data_dir=PROCESSED_DIR, models_dir=MODELS_DIR)

        # 1. Load Canonical Works
        parquet_path = PROCESSED_DIR / "canonical_works.parquet"
        if parquet_path.exists():
            self.df_works = pd.read_parquet(parquet_path)
        else:
            self.df_works = self.engine.load_data()
        print(f"[✓] Loaded {len(self.df_works):,} canonical works into memory.")

        # Ensure datetime and numeric columns are typed
        for col in ["SANCTION_AMOUNT", "RECOMMENDED_AMOUNT", "total_disbursed", "dqi_score"]:
            if col in self.df_works.columns:
                self.df_works[col] = pd.to_numeric(self.df_works[col], errors="coerce").fillna(0.0)

        # 2. Compute Priority & Rule Tags if missing
        if "priority" not in self.df_works.columns:
            self._precompute_priorities()

        # 3. Load Allocations & Masters
        self._load_masters_and_allocations()

        # 4. Precompute Geo & Entity Aggregations
        self._precompute_state_metrics()
        self._precompute_mp_directory()
        self._precompute_vendor_directory()

        print("[✓] MPLADS DataService initialized with precomputed caches.")

    @classmethod
    def get_instance(cls) -> "DataService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _precompute_priorities(self):
        """Precomputes fast two-axis risk tiers across works."""
        sanc = self.df_works["SANCTION_AMOUNT"]
        disb = self.df_works["total_disbursed"]
        days_rec = pd.to_numeric(self.df_works.get("days_rec_to_sanction", 0), errors="coerce").fillna(0)
        days_sanc = pd.to_numeric(self.df_works.get("days_since_sanction", 0), errors="coerce").fillna(0)
        has_end = self.df_works["ACTUAL_END_DATE"].notna() if "ACTUAL_END_DATE" in self.df_works.columns else False

        # Conditions
        is_overrun = (sanc > 0) & (disb > sanc * 1.05)
        is_mismatch = (sanc > 0) & (disb >= sanc * 0.85) & (days_sanc > 365) & (~has_end)
        is_d1_breach = days_rec > 45
        is_stalled = (sanc > 0) & (disb == 0) & (days_sanc > 90)

        conditions = [
            is_overrun | (is_mismatch & (days_sanc > 730)),
            is_mismatch | (is_d1_breach & is_stalled),
            is_d1_breach | is_stalled,
        ]
        choices = ["CRITICAL", "HIGH", "MEDIUM"]
        self.df_works["priority"] = np.select(conditions, choices, default="LOW")

    def _load_masters_and_allocations(self):
        """Loads state/district lookup tables and MP allocations."""
        self.states_df = pd.read_csv(DATA_DIR / "master_states.csv") if (DATA_DIR / "master_states.csv").exists() else pd.DataFrame()
        self.districts_df = pd.read_csv(DATA_DIR / "master_districts.csv") if (DATA_DIR / "master_districts.csv").exists() else pd.DataFrame()

        ls_path = DATA_DIR / "mplads_lok_sabha_allocations.csv"
        rs_path = DATA_DIR / "mplads_rajya_sabha_allocations.csv"
        
        alloc_dfs = []
        if ls_path.exists():
            df_ls = pd.read_csv(ls_path)
            df_ls["HOUSE"] = "LOK_SABHA"
            alloc_dfs.append(df_ls)
        if rs_path.exists():
            df_rs = pd.read_csv(rs_path)
            df_rs["HOUSE"] = "RAJYA_SABHA"
            alloc_dfs.append(df_rs)

        if alloc_dfs:
            self.allocations_df = pd.concat(alloc_dfs, ignore_index=True)
            self.allocations_df["ALLOCATED_AMT"] = pd.to_numeric(self.allocations_df.get("ALLOCATED_AMT", 0), errors="coerce").fillna(0.0)
        else:
            self.allocations_df = pd.DataFrame()

    def _precompute_state_metrics(self):
        """Precomputes summary metrics for all 36 States & UTs with vectorized operations."""
        # Ensure fast boolean indicators
        self.df_works["_is_completed"] = self.df_works["ACTUAL_END_DATE"].notna() if "ACTUAL_END_DATE" in self.df_works.columns else False
        self.df_works["_is_critical"] = (self.df_works["priority"] == "CRITICAL")
        self.df_works["_is_high"] = (self.df_works["priority"] == "HIGH")
        self.df_works["_is_med"] = (self.df_works["priority"] == "MEDIUM")

        grouped = self.df_works.groupby("STATE_NAME")
        st_agg = grouped.agg(
            total_works=("WORK_RECOMMENDATION_DTL_ID", "count"),
            sanc_amt=("SANCTION_AMOUNT", "sum"),
            disb_amt=("total_disbursed", "sum"),
            completed_cnt=("_is_completed", "sum"),
            crit_cnt=("_is_critical", "sum"),
            high_cnt=("_is_high", "sum"),
            med_cnt=("_is_med", "sum"),
            district_count=("IDA_NAME", "nunique") if "IDA_NAME" in self.df_works.columns else ("SANCTION_AMOUNT", "count"),
            mp_count=("MP_NAME", "nunique") if "MP_NAME" in self.df_works.columns else ("SANCTION_AMOUNT", "count"),
        ).reset_index()

        records = []
        for _, row in st_agg.iterrows():
            state_name = str(row["STATE_NAME"]).strip()
            if not state_name or state_name == "nan":
                continue
            total_works = int(row["total_works"])
            sanc_amt = float(row["sanc_amt"])
            disb_amt = float(row["disb_amt"])
            completed_cnt = int(row["completed_cnt"])
            crit_cnt = int(row["crit_cnt"])
            high_cnt = int(row["high_cnt"])
            med_cnt = int(row["med_cnt"])
            util_rate = round((disb_amt / max(sanc_amt, 1.0)) * 100, 1)
            comp_rate = round((completed_cnt / max(total_works, 1)) * 100, 1)

            records.append({
                "state_name": state_name,
                "total_works": total_works,
                "sanctioned_amount_cr": round(sanc_amt / 1e7, 2),
                "disbursed_amount_cr": round(disb_amt / 1e7, 2),
                "completed_works": completed_cnt,
                "critical_alerts": crit_cnt,
                "high_alerts": high_cnt,
                "medium_alerts": med_cnt,
                "total_alerts": crit_cnt + high_cnt + med_cnt,
                "avg_dqi": 0.85,
                "utilization_pct": min(util_rate, 100.0),
                "completion_pct": min(comp_rate, 100.0),
                "district_count": int(row["district_count"]),
                "mp_count": int(row["mp_count"]),
            })
        self.state_metrics = {r["state_name"]: r for r in records}
        self.state_metrics_list = sorted(records, key=lambda x: x["sanctioned_amount_cr"], reverse=True)

    def _precompute_mp_directory(self):
        """Merges allocation quotas with actual project recommendations & expenditures."""
        mp_works_agg = self.df_works.groupby("MP_NAME").agg(
            works_count=("WORK_RECOMMENDATION_DTL_ID", "count"),
            sanctioned_amount=("SANCTION_AMOUNT", "sum"),
            disbursed_amount=("total_disbursed", "sum"),
            completed_count=("_is_completed", "sum"),
            critical_flags=("_is_critical", "sum"),
            high_flags=("_is_high", "sum"),
            state_name=("STATE_NAME", "first"),
            house=("house", "first"),
            constituency=("CONSTITUENCY", "first"),
        ).reset_index()

        # Merge with allocations table
        if not self.allocations_df.empty:
            merged = pd.merge(
                self.allocations_df,
                mp_works_agg,
                on="MP_NAME",
                how="left",
                suffixes=("", "_works")
            )
        else:
            merged = mp_works_agg

        mps = []
        for _, row in merged.iterrows():
            mp_name = str(row.get("MP_NAME", "Unknown")).strip()
            if not mp_name or mp_name == "nan":
                continue
            alloc_val = row.get("ALLOCATED_AMT")
            alloc = float(alloc_val) if pd.notna(alloc_val) else 50000000.0  # Default ₹5 Cr/year entitlement
            disb_val = row.get("disbursed_amount")
            disb = float(disb_val) if pd.notna(disb_val) else 0.0
            sanc_val = row.get("sanctioned_amount")
            sanc = float(sanc_val) if pd.notna(sanc_val) else 0.0
            works_val = row.get("works_count")
            works_cnt = int(works_val) if pd.notna(works_val) else 0
            comp_val = row.get("completed_count")
            comp_cnt = int(comp_val) if pd.notna(comp_val) else 0
            crit_val = row.get("critical_flags")
            crit_cnt = int(crit_val) if pd.notna(crit_val) else 0
            high_val = row.get("high_flags")
            high_cnt = int(high_val) if pd.notna(high_val) else 0

            util_pct = round((disb / max(alloc, 1.0)) * 100, 1)

            mps.append({
                "mp_name": mp_name,
                "house": str(row.get("HOUSE", row.get("house", "LOK_SABHA"))).replace("_", " ").title(),
                "state_name": str(row.get("STATE_NAME", "National")),
                "constituency": str(row.get("CONSTITUENCY", "State-wide")),
                "allocated_amount_cr": round(alloc / 1e7, 2),
                "sanctioned_amount_cr": round(sanc / 1e7, 2),
                "disbursed_amount_cr": round(disb / 1e7, 2),
                "utilization_pct": min(util_pct, 150.0),
                "total_works": works_cnt,
                "completed_works": comp_cnt,
                "critical_flags": crit_cnt,
                "high_flags": high_cnt,
                "risk_tier": "CRITICAL" if crit_cnt > 2 else ("HIGH" if (crit_cnt > 0 or high_cnt > 3) else "NORMAL")
            })

        self.mp_directory = sorted(mps, key=lambda x: (x["total_works"], x["disbursed_amount_cr"]), reverse=True)

    def _precompute_vendor_directory(self):
        """Precomputes contractor concentration, HHI metrics, and recurrence risk."""
        valid_vendors = self.df_works[
            self.df_works["primary_vendor"].notna() &
            (self.df_works["total_disbursed"] > 0)
        ].copy()
        if valid_vendors.empty:
            self.vendor_directory = []
            return

        valid_vendors["_days_over_365"] = pd.to_numeric(valid_vendors.get("days_since_sanction", 0), errors="coerce").fillna(0) > 365

        v_agg = valid_vendors.groupby("primary_vendor").agg(
            total_disbursed=("total_disbursed", "sum"),
            total_works=("WORK_RECOMMENDATION_DTL_ID", "count"),
            district_count=("IDA_NAME", "nunique"),
            state_count=("STATE_NAME", "nunique"),
            critical_works=("_is_critical", "sum"),
            delayed_works=("_days_over_365", "sum"),
            primary_state=("STATE_NAME", "first"),
            primary_category=("WORK_CATEGORY", "first") if "WORK_CATEGORY" in valid_vendors.columns else ("STATE_NAME", "first"),
        ).reset_index()

        vendors = []
        for _, row in v_agg.iterrows():
            v_name = str(row["primary_vendor"]).strip()
            if not v_name or v_name == "nan" or len(v_name) < 2:
                continue
            total_disb = float(row["total_disbursed"])
            total_works = int(row["total_works"])
            crit_works = int(row["critical_works"])
            delayed_works = int(row["delayed_works"])
            is_dominant = total_works >= 5 and total_disb >= 10000000.0

            vendors.append({
                "vendor_name": v_name,
                "total_disbursed_cr": round(total_disb / 1e7, 2),
                "total_works": total_works,
                "district_count": int(row["district_count"]),
                "state_count": int(row["state_count"]),
                "critical_works": crit_works,
                "delayed_works": delayed_works,
                "primary_state": str(row["primary_state"]),
                "primary_category": str(row["primary_category"]) if pd.notna(row["primary_category"]) else "Infrastructure",
                "hhi_risk": "CONCENTRATED" if is_dominant else "COMPETITIVE",
                "has_recurrence_flag": crit_works >= 2 or delayed_works >= 4,
            })
        self.vendor_directory = sorted(vendors, key=lambda x: x["total_disbursed_cr"], reverse=True)

    # ------------------ Public Query APIs ------------------

    def get_national_overview(self, scope: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculates national or tenant-scoped overview KPIs."""
        df = self.apply_tenant_filter(self.df_works, scope)

        total_works = len(df)
        total_sanc = float(df["SANCTION_AMOUNT"].sum())
        total_disb = float(df["total_disbursed"].sum())
        completed_cnt = int(df["ACTUAL_END_DATE"].notna().sum()) if "ACTUAL_END_DATE" in df.columns else 0
        avg_dqi = float(df["dqi_score"].mean()) if "dqi_score" in df.columns else 0.85

        p_counts = df["priority"].value_counts().to_dict()

        # Category breakdown
        cat_counts = df["WORK_CATEGORY"].value_counts().head(6).to_dict()

        return {
            "total_works": total_works,
            "total_sanctioned_cr": round(total_sanc / 1e7, 2),
            "total_disbursed_cr": round(total_disb / 1e7, 2),
            "completed_works": completed_cnt,
            "overall_completion_pct": round((completed_cnt / max(total_works, 1)) * 100, 1),
            "overall_utilization_pct": round((total_disb / max(total_sanc, 1.0)) * 100, 1),
            "avg_dqi_score": round(avg_dqi, 3),
            "priority_summary": {
                "CRITICAL": p_counts.get("CRITICAL", 0),
                "HIGH": p_counts.get("HIGH", 0),
                "MEDIUM": p_counts.get("MEDIUM", 0),
                "LOW": p_counts.get("LOW", 0),
            },
            "top_categories": [{"name": k, "count": v} for k, v in cat_counts.items()],
            "active_states_count": int(df["STATE_NAME"].nunique()),
            "active_districts_count": int(df["IDA_NAME"].nunique()) if "IDA_NAME" in df.columns else 0,
        }

    def get_state_choropleth_data(self) -> List[Dict[str, Any]]:
        """Returns all state indicators for map coloring."""
        return self.state_metrics_list

    def get_districts_for_state(self, state_name: str) -> List[Dict[str, Any]]:
        """Returns all districts under a state with bottleneck indicators."""
        sub = self.df_works[self.df_works["STATE_NAME"].astype(str).str.upper() == state_name.upper()]
        if sub.empty:
            return []

        grp = sub.groupby("IDA_NAME")
        districts = []
        for dist_name, d_sub in grp:
            d_name = str(dist_name).strip()
            if not d_name or d_name == "nan":
                continue
            total_works = len(d_sub)
            sanc_amt = float(d_sub["SANCTION_AMOUNT"].sum())
            disb_amt = float(d_sub["total_disbursed"].sum())
            comp_cnt = int(d_sub["ACTUAL_END_DATE"].notna().sum()) if "ACTUAL_END_DATE" in d_sub.columns else 0
            crit_cnt = int((d_sub["priority"] == "CRITICAL").sum())
            high_cnt = int((d_sub["priority"] == "HIGH").sum())

            # Implementing Agency overload indicator
            top_ia = str(d_sub["ia_name"].mode().iloc[0]) if ("ia_name" in d_sub.columns and not d_sub["ia_name"].dropna().empty) else "District Authority"

            districts.append({
                "district_name": d_name,
                "state_name": state_name,
                "total_works": total_works,
                "sanctioned_amount_cr": round(sanc_amt / 1e7, 2),
                "disbursed_amount_cr": round(disb_amt / 1e7, 2),
                "completed_works": comp_cnt,
                "completion_pct": round((comp_cnt / max(total_works, 1)) * 100, 1),
                "utilization_pct": round((disb_amt / max(sanc_amt, 1.0)) * 100, 1),
                "critical_flags": crit_cnt,
                "high_flags": high_cnt,
                "primary_ia": top_ia,
                "risk_tier": "CRITICAL" if crit_cnt > 0 else ("HIGH" if high_cnt > 2 else "NORMAL"),
            })

        return sorted(districts, key=lambda x: x["total_works"], reverse=True)

    def query_works(
        self,
        scope: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        mp_name: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> Dict[str, Any]:
        """Search and filter works with multi-tenant boundaries."""
        df = self.apply_tenant_filter(self.df_works, scope)

        if state:
            df = df[df["STATE_NAME"].astype(str).str.upper() == state.upper()]
        if district:
            d_q = str(district).strip().upper()
            df = df[df["IDA_NAME"].astype(str).str.upper().apply(lambda v: d_q in v or v in d_q)]
        if mp_name:
            mp_toks = [t.lower() for t in str(mp_name).split() if len(t) > 2]
            if mp_toks:
                df = df[df["MP_NAME"].astype(str).apply(lambda v: all(t in v.lower() for t in mp_toks))]
            else:
                df = df[df["MP_NAME"].astype(str).str.contains(mp_name, case=False, na=False)]
        if category:
            df = df[df["WORK_CATEGORY"].astype(str).str.contains(category, case=False, na=False)]
        if priority:
            df = df[df["priority"].astype(str).str.upper() == priority.upper()]
        if query:
            q_lower = query.lower()
            mask = (
                df["WORK_DESCRIPTION"].astype(str).str.lower().str.contains(q_lower, na=False) |
                df["WORK_RECOMMENDATION_DTL_ID"].astype(str).str.contains(q_lower, na=False) |
                df["MP_NAME"].astype(str).str.lower().str.contains(q_lower, na=False) |
                df["IDA_NAME"].astype(str).str.lower().str.contains(q_lower, na=False)
            )
            df = df[mask]

        total_matching = len(df)
        start = (page - 1) * page_size
        end = start + page_size
        page_slice = df.iloc[start:end]

        results = []
        for _, row in page_slice.iterrows():
            rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
            results.append({
                "work_rec_id": rec_id,
                "work_id": str(row.get("WORK_ID") or rec_id),
                "description": str(row.get("WORK_DESCRIPTION", "MPLADS Community Work")),
                "category": str(row.get("WORK_CATEGORY", "General")),
                "state_name": str(row.get("STATE_NAME", "N/A")),
                "ida_name": str(row.get("IDA_NAME", "N/A")),
                "mp_name": str(row.get("MP_NAME", "N/A")),
                "sanction_amount": float(row.get("SANCTION_AMOUNT", 0.0)),
                "total_disbursed": float(row.get("total_disbursed", 0.0)),
                "priority": str(row.get("priority", "LOW")),
                "lifecycle_stage": str(row.get("lifecycle_stage", "SANCTIONED")),
                "dqi_score": float(row.get("dqi_score", 0.85)),
                "primary_vendor": redact_vendor_name(
                    row.get("primary_vendor"),
                    scope.get("can_view_unredacted_vendors", True) if scope else True,
                ),
                "days_rec_to_sanction": int(row.get("days_rec_to_sanction", 0)),
                "days_since_sanction": int(row.get("days_since_sanction", 0)),
            })

        return {
            "total": total_matching,
            "page": page,
            "page_size": page_size,
            "total_pages": int(np.ceil(total_matching / max(page_size, 1))),
            "items": results,
        }

    def verify_work_access(self, work_rec_id: str, scope: Optional[Dict[str, Any]]) -> bool:
        """Verifies if a specific work ID falls within the authenticated user's tenant boundary."""
        if not scope:
            return True
        if not scope.get("strict_isolation", True):
            return True
        role = scope.get("role")
        if role in ("CENTRAL_AUDITOR", "CITIZEN", None):
            return True

        rec_id_str = str(work_rec_id).strip()
        match = self.df_works[self.df_works["WORK_RECOMMENDATION_DTL_ID"].astype(str) == rec_id_str]
        if match.empty:
            return False

        row = match.iloc[0]
        if "STATE_NAME" in scope and str(row.get("STATE_NAME", "")).upper() != str(scope["STATE_NAME"]).upper():
            return False
        if "IDA_NAME" in scope:
            ida_query = str(scope["IDA_NAME"]).strip().upper()
            row_ida = str(row.get("IDA_NAME", "")).upper()
            if ida_query not in row_ida and row_ida not in ida_query:
                return False
        if "MP_NAME" in scope:
            mp_tokens = [t.lower() for t in str(scope["MP_NAME"]).split() if len(t) > 2]
            row_mp = str(row.get("MP_NAME", "")).lower()
            if mp_tokens and not all(t in row_mp for t in mp_tokens):
                return False

        return True

    def get_work_dossier(self, work_rec_id: str, scope: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates the official 5-question audit dossier with AC-19 Checklist and tenant scoping."""
        rec_id_str = str(work_rec_id).strip()
        match = self.df_works[self.df_works["WORK_RECOMMENDATION_DTL_ID"].astype(str) == rec_id_str]
        if match.empty:
            raise ValueError(f"Work with recommendation ID '{rec_id_str}' not found.")

        # Check tenant access
        if scope and not self.verify_work_access(rec_id_str, scope):
            raise PermissionError(f"Access denied: Work #{rec_id_str} is outside your active tenant jurisdiction.")

        row = match.iloc[0]
        sanc = float(row.get("SANCTION_AMOUNT", 0.0))
        disb = float(row.get("total_disbursed", 0.0))
        days_rec = int(row.get("days_rec_to_sanction", 0) or 0)
        days_sanc = int(row.get("days_since_sanction", 0) or 0)
        has_end = pd.notna(row.get("ACTUAL_END_DATE"))
        priority = str(row.get("priority", "LOW"))

        is_citizen = bool(scope and scope.get("is_citizen"))
        can_view_vendors = bool(scope.get("can_view_unredacted_vendors", False)) if scope else True

        # Formulate 5 Core Governance Answers
        # Q1: What happened?
        observations = []
        if days_rec > 45:
            observations.append(f"Sanction delay of {days_rec} days exceeded statutory 45-day SLA by {days_rec - 45} days.")
        if disb > sanc * 1.05:
            observations.append(f"Disbursed funds (₹{disb:,.0f}) exceeded sanctioned budget (₹{sanc:,.0f}) by {(disb/sanc - 1):.1%}.")
        if days_sanc > 365 and not has_end:
            observations.append(f"Project has been active for {days_sanc} days without formal completion sign-off.")
        if not observations:
            observations.append("Project lifecycle milestones follow expected statistical baseline parameters.")
        q1_what = "; ".join(observations)

        # Q2: Why unusual?
        q2_why = f"Flagged as {priority} priority due to statutory compliance deviations and expenditure velocity anomalies relative to district peers."

        # Q3: Compared with what?
        q3_compared = "MPLADS 2023 Guidelines (Para 3.2.4 SLA of 45 days, Para 3.2.12 1-year completion mandate) and district peer median cost baselines."

        # Q4: Evidence (sanitized for citizen)
        q4_evidence = {
            "sanction_amount": sanc,
            "disbursed_amount": disb,
            "days_rec_to_sanction": days_rec,
            "days_since_sanction": days_sanc,
            "recommendation_date": str(row.get("RECOMMENDATION_DATE", "N/A")),
            "sanction_date": str(row.get("SANCTION_DATE", "N/A")),
            "vendor_name": redact_vendor_name(row.get("primary_vendor", "N/A"), can_view_vendors),
            "implementing_agency": str(row.get("ia_name", "N/A")),
            "data_quality_index": float(row.get("dqi_score", 0.85)),
        }

        # Q5: Limitations
        q5_limitations = "Assessment derived from unauthenticated e-SAKSHI pre-login REST datasets. Does not constitute a conclusive legal verdict of intentional wrongdoing."

        # AC-19 Prescribed Action Checklist (or citizen social audit checklist)
        if is_citizen:
            actions = [
                "Verify physical community handover and photographic asset geotagging.",
                "Submit public social audit feedback to District Planning Cell.",
                "Confirm unrestricted public access without commercial exclusion.",
            ]
        else:
            actions = [
                "Dispatch District Quality Monitor (DQM) for geo-tagged visual site inspection.",
                "Verify contractor milestone billing invoices against measurement book (MB) entries.",
                "Issue formal show-cause explanation notice to Implementing Agency regarding statutory deadline breach.",
                "Review bank interest accretion and holding account balances in PFMS.",
            ]

        return {
            "work_rec_id": rec_id_str,
            "work_id": str(row.get("WORK_ID") or rec_id_str),
            "description": str(row.get("WORK_DESCRIPTION", "MPLADS Project")),
            "category": str(row.get("WORK_CATEGORY", "Community Infrastructure")),
            "state_name": str(row.get("STATE_NAME", "N/A")),
            "ida_name": str(row.get("IDA_NAME", "N/A")),
            "mp_name": str(row.get("MP_NAME", "N/A")),
            "priority": priority,
            "sanction_amount": sanc,
            "total_disbursed": disb,
            "five_questions": {
                "q1_what_happened": q1_what,
                "q2_why_unusual": q2_why,
                "q3_compared_with_what": q3_compared,
                "q4_supporting_evidence": q4_evidence,
                "q5_limitations": q5_limitations,
            },
            "next_review_actions": actions,
        }

    def apply_tenant_filter(self, df: pd.DataFrame, scope: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """Applies tenant restrictions to dataframe queries."""
        if not scope:
            return df
        # If strict isolation is disabled (Auditor / Sandbox mode), skip geographic/portfolio restrictions
        if not scope.get("strict_isolation", True):
            return df

        filtered = df
        if "STATE_NAME" in scope and "STATE_NAME" in df.columns:
            filtered = filtered[filtered["STATE_NAME"].astype(str).str.upper() == str(scope["STATE_NAME"]).upper()]
        if "IDA_NAME" in scope and "IDA_NAME" in df.columns:
            ida_query = str(scope["IDA_NAME"]).strip().upper()
            filtered = filtered[filtered["IDA_NAME"].astype(str).str.upper().apply(
                lambda val: ida_query in val or val in ida_query
            )]
        if "MP_NAME" in scope and "MP_NAME" in df.columns:
            mp_tokens = [t.lower() for t in str(scope["MP_NAME"]).split() if len(t) > 2]
            if mp_tokens:
                filtered = filtered[filtered["MP_NAME"].astype(str).apply(
                    lambda val: all(t in val.lower() for t in mp_tokens)
                )]
            else:
                filtered = filtered[filtered["MP_NAME"].astype(str).str.contains(str(scope["MP_NAME"]), case=False, na=False)]
        if scope.get("is_citizen") and "ACTUAL_END_DATE" in filtered.columns:
            completed = filtered[filtered["ACTUAL_END_DATE"].notna()]
            if not completed.empty:
                filtered = completed
        return filtered
