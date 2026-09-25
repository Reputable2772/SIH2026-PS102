"""
Natural-Language Analytics Assistant (Pillar 15).
Translates plain English queries into structured filters and aggregate governance metrics.

Supports entity extraction for:
  - MP names (with honorific / year-suffix normalization)
  - Parliamentary constituencies (with SC/ST suffix normalization)
  - Districts (IDA_NAME)
  - Parliamentary Houses (Lok Sabha / Rajya Sabha)
  - All 11 canonical MPLADS work categories with rich keyword mappings
  - States, status/delay, risk/priority, and sanction amount ranges
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from backend.services.data_service import DataService

# ---------------------------------------------------------------------------
# Honorific / suffix patterns used to normalize MP names
# ---------------------------------------------------------------------------
_HONORIFIC_RE = re.compile(
    r"^(?:shri|smt\.?|dr\.?|adv\.?|prof\.?|km\.?|sushri|hon\.?|honourable|hon'ble)\s+",
    re.IGNORECASE,
)
_YEAR_SUFFIX_RE = re.compile(r"\s*\(\d{4}[-–]\d{2,4}\)\s*")

# Pattern to strip SC/ST reservation tags from constituency names
_RESERVATION_TAG_RE = re.compile(r"\s*\((sc|st)\)\s*", re.IGNORECASE)

# Words that must never match as entity names on their own
_STOPWORDS: Set[str] = {
    "show", "find", "get", "list", "display", "search", "query", "all",
    "works", "work", "projects", "project", "in", "for", "of", "by",
    "the", "a", "an", "and", "or", "with", "from", "to", "above",
    "below", "more", "less", "than", "greater", "under", "between",
    "delayed", "delay", "stalled", "stopped", "completed", "critical",
    "high", "risk", "flagged", "anomaly", "priority", "lakh", "lac",
    "crore", "cr", "cost", "overrun", "turnaround", "exceeding",
    "recommended", "recommend", "sanction", "sanctioned", "disbursed",
    "fund", "utilization", "road", "water", "school", "hospital",
    "solar", "drain", "community", "hall", "bridge", "education",
    "health", "drinking", "irrigation", "lighting", "repair",
    "renovation", "trust", "society", "amenities", "anganwadi",
    "sports", "stadium", "cctv", "security", "divyang", "accessibility",
    "lok", "sabha", "rajya", "mp", "constituency", "district", "state",
    "not", "no", "is", "are", "was", "were", "has", "have", "had",
    "total", "average", "highest", "lowest", "top", "bottom",
}

# ---------------------------------------------------------------------------
# Canonical category keyword map  (query keyword -> WORK_CATEGORY value)
# Longer multi-word keywords are checked first to avoid partial matches.
# ---------------------------------------------------------------------------
_CATEGORY_MAP: Dict[str, Tuple[str, List[str]]] = {
    "Roads & Pathways": (
        "Roads & Pathways",
        [
            "cc road", "tar road", "link road", "rcc drain", "road",
            "pathway", "culvert", "pavement", "bridge", "connectivity",
        ],
    ),
    "Drinking Water": (
        "Drinking Water",
        [
            "drinking water", "water supply", "ro plant", "borewell",
            "hand pump", "water tank", "pipeline", "purification",
            "jal", "tanker",
        ],
    ),
    "Solar & Lighting": (
        "Solar & Lighting",
        [
            "street light", "high mast", "led light", "solar",
            "lighting", "electrification",
        ],
    ),
    "Education & Schools": (
        "Education & Schools",
        [
            "smart class", "school", "classroom", "college", "library",
            "education", "vidyalaya", "hostel", "reading room",
        ],
    ),
    "Public Health": (
        "Public Health",
        [
            "hospital", "health centre", "health center", "dispensary",
            "ambulance", "phc", "chc", "clinic", "medical", "ayush",
            "health", "wellness",
        ],
    ),
    "Community Infrastructure": (
        "Community Infrastructure",
        [
            "community hall", "community center", "community centre",
            "samaj bhavan", "barat ghar", "multipurpose", "gymnasium",
            "open gym", "crematorium", "burial", "samudayik", "shed",
            "community", "gym", "hall", "stadium",
        ],
    ),
    "Sanitation & Drainage": (
        "Sanitation & Drainage",
        [
            "drainage", "sewerage", "shauchalaya", "sanitation",
            "toilet", "drain", "swachh",
        ],
    ),
    "Irrigation & Water Conservation": (
        "Irrigation & Water Conservation",
        [
            "water conservation", "check dam", "irrigation", "canal",
            "tubewell", "bund", "watershed", "flood", "pond", "lake",
            "dam",
        ],
    ),
    "Public Amenities": (
        "Public Amenities",
        [
            "passenger shelter", "bus stand", "public park",
            "crematorium", "shamshan", "kabristan", "graveyard",
            "amenities", "park", "shelter",
        ],
    ),
    "Repair and Renovation": (
        "Repair and Renovation",
        [
            "repair", "renovation", "restoration", "maintenance",
            "reconstruction",
        ],
    ),
    "Trust and Society": (
        "Trust and Society",
        [
            "registered society", "trust", "society", "ngo",
        ],
    ),
}

# Pre-sort keywords longest-first so multi-word phrases match before fragments.
for _cat_name, (_canon, _kws) in _CATEGORY_MAP.items():
    _kws.sort(key=len, reverse=True)


class NaturalQueryService:
    _instance: Optional["NaturalQueryService"] = None

    def __init__(self):
        self.ds = DataService.get_instance()
        self._build_entity_caches()

    @classmethod
    def get_instance(cls) -> "NaturalQueryService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Cache builders (run once on singleton init)
    # ------------------------------------------------------------------

    def _build_entity_caches(self) -> None:
        """Precompute normalized lookup dictionaries for sub-ms entity matching."""
        df = self.ds.df_works

        # --- MP name cache ---
        # Maps normalized (lowercased, honorific/year-stripped) name -> canonical MP_NAME
        self._mp_cache: Dict[str, str] = {}
        for mp in df["MP_NAME"].dropna().unique():
            canonical = str(mp).strip()
            if not canonical:
                continue
            norm = _HONORIFIC_RE.sub("", canonical)
            norm = _YEAR_SUFFIX_RE.sub("", norm).strip().lower()
            if norm and norm not in _STOPWORDS and len(norm) > 2:
                self._mp_cache[norm] = canonical

        # --- Constituency cache ---
        # Maps normalized (lowercased, SC/ST-stripped) name -> canonical CONSTITUENCY
        self._constituency_cache: Dict[str, str] = {}
        for const in df["CONSTITUENCY"].dropna().unique():
            canonical = str(const).strip()
            if not canonical:
                continue
            norm = _RESERVATION_TAG_RE.sub("", canonical).strip().lower()
            if norm and norm not in _STOPWORDS and len(norm) > 2:
                self._constituency_cache[norm] = canonical

        # --- District cache ---
        self._district_cache: Dict[str, str] = {}
        if "IDA_NAME" in df.columns:
            for dist in df["IDA_NAME"].dropna().unique():
                canonical = str(dist).strip()
                if not canonical:
                    continue
                norm = canonical.strip().lower()
                if norm and norm not in _STOPWORDS and len(norm) > 2:
                    self._district_cache[norm] = canonical

    # ------------------------------------------------------------------
    # Entity extraction helpers
    # ------------------------------------------------------------------

    def _extract_mp(self, text: str) -> Optional[str]:
        """Return the canonical MP_NAME if one is found in the query text."""
        # Try longest names first for greedy matching
        for norm, canonical in sorted(
            self._mp_cache.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if norm in text:
                return canonical
        return None

    def _extract_constituency(self, text: str) -> Optional[str]:
        """Return the canonical CONSTITUENCY if one is found in the query text."""
        for norm, canonical in sorted(
            self._constituency_cache.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if norm in text:
                return canonical
        return None

    def _extract_district(self, text: str) -> Optional[str]:
        """Return the canonical IDA_NAME if one is found in the query text."""
        for norm, canonical in sorted(
            self._district_cache.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if norm in text:
                return canonical
        return None

    def _extract_house(self, text: str) -> Optional[int]:
        """Return HOUSE_OF_PARLIAMENT code if mentioned. 1=Rajya Sabha, 2=Lok Sabha."""
        if "lok sabha" in text:
            return 2
        if "rajya sabha" in text:
            return 1
        return None

    def _extract_categories(self, text: str) -> List[str]:
        """Return list of canonical WORK_CATEGORY names matching query keywords."""
        matched: List[str] = []
        for canon, (_display, keywords) in _CATEGORY_MAP.items():
            for kw in keywords:
                if kw in text:
                    matched.append(canon)
                    break
        return matched

    # ------------------------------------------------------------------
    # Main query method
    # ------------------------------------------------------------------

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
        applied_filters: List[str] = []

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

        # 3. MP name extraction
        detected_mp = self._extract_mp(text)
        if detected_mp and not (scope and scope.get("role") == "MP_USER"):
            filtered = filtered[filtered["MP_NAME"] == detected_mp]
            applied_filters.append(f"MP: {detected_mp}")

        # 4. Constituency extraction
        detected_constituency = self._extract_constituency(text)
        if detected_constituency:
            filtered = filtered[filtered["CONSTITUENCY"] == detected_constituency]
            applied_filters.append(f"Constituency: {detected_constituency.title()}")

        # 5. District extraction
        detected_district = self._extract_district(text)
        if detected_district and not (scope and scope.get("role") == "DISTRICT_AUTHORITY"):
            filtered = filtered[filtered["IDA_NAME"] == detected_district]
            applied_filters.append(f"District: {detected_district}")

        # 6. Parliamentary House extraction
        detected_house = self._extract_house(text)
        if detected_house is not None:
            filtered = filtered[filtered["HOUSE_OF_PARLIAMENT"] == detected_house]
            house_label = "Lok Sabha" if detected_house == 2 else "Rajya Sabha"
            applied_filters.append(f"House: {house_label}")

        # 7. Category extraction (all 11 canonical categories)
        detected_categories = self._extract_categories(text)
        if detected_categories:
            # Filter by WORK_CATEGORY column directly (uses pre-classified categories)
            filtered = filtered[filtered["WORK_CATEGORY"].isin(detected_categories)]
            cat_labels = [c for c in detected_categories]
            applied_filters.append(f"Sector: {', '.join(cat_labels)}")

        # 8. Status / Delay extraction
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

        # 9. Risk / Priority extraction
        if "critical" in text:
            filtered = filtered[filtered["priority"] == "CRITICAL"]
            applied_filters.append("Priority: Critical")
        elif "high risk" in text or "flagged" in text or "anomaly" in text:
            filtered = filtered[filtered["priority"].isin(["CRITICAL", "HIGH"])]
            applied_filters.append("Priority: High / Critical Risk")

        # 10. Amount extraction (e.g. "above 20 lakh", "> 10 lakh", "below 5 lakh")
        above_match = re.search(r"(?:above|more than|greater than|>)\s*(\d+(?:\.\d+)?)\s*(lakh|lac|crore|cr)?", text)
        if above_match:
            val = float(above_match.group(1))
            unit = above_match.group(2) or "lakh"
            threshold = val * 10_000_000 if "cr" in unit else val * 100_000
            filtered = filtered[filtered["SANCTION_AMOUNT"] >= threshold]
            applied_filters.append(f"Sanction >= ₹{threshold:,.0f}")

        below_match = re.search(r"(?:below|less than|under|<)\s*(\d+(?:\.\d+)?)\s*(lakh|lac|crore|cr)?", text)
        if below_match:
            val = float(below_match.group(1))
            unit = below_match.group(2) or "lakh"
            threshold = val * 10_000_000 if "cr" in unit else val * 100_000
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
            filter_desc = ", ".join(applied_filters) if applied_filters else "System Wide"
            summary = (
                f"Found {total_count:,} works matching criteria ({filter_desc}). "
                f"Total Sanction: ₹{round(total_sanction / 1e5, 1)}L, "
                f"Fund Utilization: {utilization_rate}%."
            )

        # Prepare top records for display
        records: List[Dict[str, Any]] = []
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
                    "constituency": str(r.get("CONSTITUENCY", "")),
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
            "Find works recommended by Supriya Sule in Baramati",
            "Show solar lighting projects in Lok Sabha above 10 lakh",
            "Find highest risk projects in Uttar Pradesh",
            "Show irrigation and water conservation works in Bihar",
            "Find critical priority community halls in Rajya Sabha",
            "Show completed education works in Karnataka",
            "Find drinking water projects in Kadapa district",
            "Show repair and renovation works above 5 lakh",
            "Find trust and society works in Andhra Pradesh",
        ]
