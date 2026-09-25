"""
Natural-Language Analytics Assistant (Pillar 15).
Translates plain English queries into structured filters and aggregate governance metrics.
"""

import re
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.services.data_service import DataService


class NaturalQueryService:
    _instance: Optional["NaturalQueryService"] = None

    def __init__(self):
        self.ds = DataService.get_instance()

    @classmethod
    def get_instance(cls) -> "NaturalQueryService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def query(
        self,
        query_text: str,
        scope: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Parses natural language query, filters DataFrame, and aggregates results."""
        df = self.ds.df_works
        if df.empty:
            return {"summary": "No data available in system.", "count": 0, "results": [], "metrics": {}}

        text = query_text.lower().strip()
        filtered = df
        applied_filters = []

        # 1. Multi-Tenant RBAC Enforcement
        if scope and scope.get("strict_isolation", True):
            role = scope.get("role")
            if role == "DISTRICT_AUTHORITY":
                u_dist = str(scope.get("IDA_NAME", "")).strip().upper()
                filtered = filtered[filtered["_ida_upper"].apply(lambda v: u_dist in str(v) or str(v) in u_dist)]
                applied_filters.append(f"District restricted to {scope.get('IDA_NAME')}")
            elif role == "STATE_NODAL_OFFICER":
                u_state = str(scope.get("STATE_NAME", "")).strip().upper()
                filtered = filtered[filtered["_state_upper"] == u_state]
                applied_filters.append(f"State restricted to {scope.get('STATE_NAME')}")
            elif role == "MP_USER":
                u_mp = str(scope.get("MP_NAME", "")).strip().lower()
                filtered = filtered[filtered["MP_NAME"].astype(str).str.lower().str.contains(u_mp, na=False)]
                applied_filters.append(f"MP restricted to {scope.get('MP_NAME')}")

        # 2. State extraction
        detected_state = None
        for st in self.ds._state_districts_cache.keys():
            if st.lower() in text:
                detected_state = st
                break

        if detected_state and not (scope and scope.get("role") == "STATE_NODAL_OFFICER"):
            filtered = filtered[filtered["_state_upper"] == detected_state]
            applied_filters.append(f"State: {detected_state.title()}")

        # 3. Category extraction
        categories = {
            "road": ["road", "cc road", "tar", "path", "bridge", "connectivity"],
            "water": ["water", "drinking water", "borewell", "tank", "pipeline", "ro plant", "purification"],
            "education": ["school", "classroom", "college", "library", "education", "smart class"],
            "health": ["hospital", "clinic", "dispensary", "health", "ambulance", "phc", "wellness"],
            "sanitation": ["drain", "drainage", "toilet", "sanitation", "swachh"],
            "electricity": ["solar", "light", "street light", "electrification", "power"],
            "community": ["community", "hall", "samaj", "bhavan", "shed", "gym"],
        }
        for cat_name, keywords in categories.items():
            if any(k in text for k in keywords):
                cat_mask = (
                    filtered["WORK_DESCRIPTION"]
                    .fillna("")
                    .astype(str)
                    .str.lower()
                    .str.contains("|".join(keywords), regex=True)
                )
                filtered = filtered[cat_mask]
                applied_filters.append(f"Sector: {cat_name.title()}")
                break

        # 4. Status / Delay extraction
        t_col = "days_rec_to_sanction" if "days_rec_to_sanction" in filtered.columns else "days_since_sanction"
        if "delayed" in text or "delay" in text:
            turnarounds = pd.to_numeric(filtered[t_col], errors="coerce").fillna(0)
            filtered = filtered[turnarounds > 90]
            applied_filters.append("Delayed (> 90 days)")
        elif "stalled" in text or "stopped" in text:
            turnarounds = pd.to_numeric(filtered[t_col], errors="coerce").fillna(0)
            filtered = filtered[turnarounds > 180]
            applied_filters.append("Severely Stalled (> 180 days)")
        elif "completed" in text:
            if "status_std" in filtered.columns:
                filtered = filtered[filtered["status_std"] == "COMPLETED"]
            applied_filters.append("Status: Completed")

        # 5. Risk / Priority extraction
        if "critical" in text:
            filtered = filtered[filtered["priority"] == "CRITICAL"]
            applied_filters.append("Priority: Critical")
        elif "high risk" in text or "flagged" in text or "anomaly" in text:
            filtered = filtered[filtered["priority"].isin(["CRITICAL", "HIGH"])]
            applied_filters.append("Priority: High / Critical Risk")

        # 6. Amount extraction (e.g. "above 20 lakh", "> 10 lakh", "below 5 lakh")
        above_match = re.search(r"(?:above|more than|greater than|>)\s*(\d+(?:\.\d+)?)\s*(lakh|lac|crore|cr)?", text)
        if above_match:
            val = float(above_match.group(1))
            unit = above_match.group(2) or "lakh"
            threshold = val * 10000000 if "cr" in unit else val * 100000
            filtered = filtered[filtered["SANCTION_AMOUNT"] >= threshold]
            applied_filters.append(f"Sanction >= ₹{threshold:,.0f}")

        below_match = re.search(r"(?:below|less than|under|<)\s*(\d+(?:\.\d+)?)\s*(lakh|lac|crore|cr)?", text)
        if below_match:
            val = float(below_match.group(1))
            unit = below_match.group(2) or "lakh"
            threshold = val * 10000000 if "cr" in unit else val * 100000
            filtered = filtered[filtered["SANCTION_AMOUNT"] <= threshold]
            applied_filters.append(f"Sanction <= ₹{threshold:,.0f}")

        # Metrics computation
        total_count = len(filtered)
        total_sanction = float(filtered["SANCTION_AMOUNT"].sum())
        total_disbursed = float(filtered["total_disbursed"].sum())
        avg_delay = float(pd.to_numeric(filtered[t_col], errors="coerce").mean() or 0.0)
        critical_count = int((filtered["priority"] == "CRITICAL").sum())
        utilization_rate = round((total_disbursed / total_sanction * 100) if total_sanction > 0 else 0.0, 1)

        if total_count == 0:
            summary = "No works found matching your criteria. Try loosening filters."
        else:
            summary = f"Found {total_count:,} works matching criteria ({', '.join(applied_filters) if applied_filters else 'System Wide'}). Total Sanction: ₹{round(total_sanction / 1e5, 1)}L, Fund Utilization: {utilization_rate}%."

        # Prepare top records for display
        records = []
        sample = filtered.head(limit)
        for _, r in sample.iterrows():
            rec_id = str(r.get("WORK_RECOMMENDATION_DTL_ID"))
            records.append(
                {
                    "work_rec_id": rec_id,
                    "description": str(r.get("WORK_DESCRIPTION", "N/A")),
                    "state_name": str(r.get("STATE_NAME", "")),
                    "district_name": str(r.get("IDA_NAME", "")),
                    "mp_name": str(r.get("MP_NAME", "")),
                    "sanction_amount": float(r.get("SANCTION_AMOUNT", 0.0)),
                    "total_disbursed": float(r.get("total_disbursed", 0.0)),
                    "turnaround_days": int(r.get(t_col, 0) or 0),
                    "priority": str(r.get("priority", "LOW")),
                    "status": str(r.get("status_std", "UNDER_EXECUTION")),
                }
            )

        return {
            "query": query_text,
            "parsed_filters": applied_filters,
            "summary": summary,
            "count": total_count,
            "metrics": {
                "total_sanctioned": round(total_sanction, 2),
                "total_disbursed": round(total_disbursed, 2),
                "utilization_pct": utilization_rate,
                "avg_turnaround_days": round(avg_delay, 1),
                "critical_risk_count": critical_count,
            },
            "results": records,
        }

    def get_suggestions(self) -> List[str]:
        """Provides natural query suggestion chips."""
        return [
            "Show delayed road works in Maharashtra above 20 lakh",
            "Find highest risk projects in Uttar Pradesh",
            "Show drinking water projects with cost overruns",
            "Find critical priority community halls in Bihar",
            "Show completed education works in Karnataka",
            "Find works with turnaround exceeding 180 days",
        ]
