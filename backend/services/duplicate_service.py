"""
Duplicate & Ghost Work Detection Service (Pillar 4).
Compares projects across description similarity, amount, location, category, and timeline.
"""

from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from backend.services.data_service import DataService


class DuplicateService:
    _instance: Optional["DuplicateService"] = None

    def __init__(self):
        self.ds = DataService.get_instance()
        self._candidate_pairs: List[Dict[str, Any]] = []
        from backend.services.audit_service import AuditService

        self._resolutions: Dict[str, Dict[str, Any]] = (
            AuditService.get_instance().get_all_duplicate_resolutions()
        )
        self._precompute_candidates()

    @classmethod
    def get_instance(cls) -> "DuplicateService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _precompute_candidates(self):
        """Scans representative project clusters to identify potential duplicate/ghost work pairs."""
        df = self.ds.df_works
        if df.empty:
            return

        # Scan across all states in master dataset for nationwide coverage
        target_states = [s.upper() for s in self.ds.state_metrics.keys()]
        if not target_states:
            target_states = list(df["_state_upper"].dropna().unique())
        pairs_found = []

        for st in target_states:
            st_df = df[df["_state_upper"] == st]
            if st_df.empty:
                continue

            state_pairs = 0
            # Group by IDA to find highly localized suspected duplicates
            for ida_name, group in st_df.groupby("_ida_upper"):
                if len(group) < 2:
                    continue
                records = group.head(40).to_dict(orient="records")
                n = len(records)

                for i in range(n):
                    d1 = str(records[i].get("WORK_DESCRIPTION", "")).strip().lower()
                    if len(d1) < 15:
                        continue
                    sanc1 = float(records[i].get("SANCTION_AMOUNT", 0.0))
                    rec_id1 = str(records[i].get("WORK_RECOMMENDATION_DTL_ID"))

                    for j in range(i + 1, min(i + 15, n)):
                        d2 = str(records[j].get("WORK_DESCRIPTION", "")).strip().lower()
                        if len(d2) < 15:
                            continue
                        sanc2 = float(records[j].get("SANCTION_AMOUNT", 0.0))
                        rec_id2 = str(records[j].get("WORK_RECOMMENDATION_DTL_ID"))

                        # Text similarity
                        text_ratio = SequenceMatcher(None, d1, d2).ratio()
                        if text_ratio < 0.70:
                            continue

                        # Amount proximity (within 20%)
                        max_sanc = max(sanc1, sanc2, 1.0)
                        amt_delta = abs(sanc1 - sanc2)
                        amt_ratio = max(0.0, 1.0 - (amt_delta / max_sanc))

                        # Category match
                        cat1 = str(records[i].get("WORK_CATEGORY", ""))
                        cat2 = str(records[j].get("WORK_CATEGORY", ""))
                        cat_ratio = 1.0 if cat1 == cat2 else 0.5

                        # Composite weighted score (0-100)
                        composite = (text_ratio * 0.50) + (amt_ratio * 0.30) + (cat_ratio * 0.20)
                        composite_pct = round(composite * 100, 1)

                        if composite_pct >= 72.0:
                            pair_id = f"DUP-{rec_id1}-{rec_id2}"
                            signals = []
                            if text_ratio >= 0.85:
                                signals.append(f"High Lexical Description Overlap ({round(text_ratio * 100)}%)")
                            else:
                                signals.append(f"Moderate Description Similarity ({round(text_ratio * 100)}%)")

                            if amt_delta == 0:
                                signals.append(f"Identical Sanction Amount (₹{sanc1:,.0f})")
                            elif amt_delta < 50000:
                                signals.append(f"Near-Identical Budget (Delta: ₹{amt_delta:,.0f})")

                            if cat1 == cat2:
                                signals.append(f"Matching Category ({cat1})")

                            vendor1 = str(records[i].get("primary_vendor", "N/A"))
                            vendor2 = str(records[j].get("primary_vendor", "N/A"))
                            if vendor1 != "N/A" and vendor1 == vendor2:
                                signals.append(f"Same Contractor Awarded ({vendor1})")

                            pairs_found.append(
                                {
                                    "pair_id": pair_id,
                                    "similarity_pct": composite_pct,
                                    "text_similarity_pct": round(text_ratio * 100, 1),
                                    "amount_similarity_pct": round(amt_ratio * 100, 1),
                                    "state_name": str(records[i].get("STATE_NAME")),
                                    "district_name": str(records[i].get("IDA_NAME")),
                                    "category": cat1,
                                    "signals": signals,
                                    "status": "PENDING_REVIEW",
                                    "project_a": {
                                        "work_rec_id": rec_id1,
                                        "description": str(records[i].get("WORK_DESCRIPTION")),
                                        "category": cat1,
                                        "sanction_amount": sanc1,
                                        "total_disbursed": float(records[i].get("total_disbursed", 0.0)),
                                        "mp_name": str(records[i].get("MP_NAME")),
                                        "ida_name": str(records[i].get("IDA_NAME")),
                                        "vendor_name": vendor1,
                                        "priority": str(records[i].get("priority", "LOW")),
                                        "recommendation_date": str(records[i].get("RECOMMENDATION_DATE", "N/A")),
                                    },
                                    "project_b": {
                                        "work_rec_id": rec_id2,
                                        "description": str(records[j].get("WORK_DESCRIPTION")),
                                        "category": cat2,
                                        "sanction_amount": sanc2,
                                        "total_disbursed": float(records[j].get("total_disbursed", 0.0)),
                                        "mp_name": str(records[j].get("MP_NAME")),
                                        "ida_name": str(records[j].get("IDA_NAME")),
                                        "vendor_name": vendor2,
                                        "priority": str(records[j].get("priority", "LOW")),
                                        "recommendation_date": str(records[j].get("RECOMMENDATION_DATE", "N/A")),
                                    },
                                }
                            )
                            state_pairs += 1
                            if state_pairs >= 15 or len(pairs_found) >= 300:
                                break
                    if state_pairs >= 15 or len(pairs_found) >= 300:
                        break
            if len(pairs_found) >= 300:
                break

        # Sort descending by similarity score
        self._candidate_pairs = sorted(pairs_found, key=lambda p: p["similarity_pct"], reverse=True)
        # Apply any previously persisted resolutions from SQLite
        for p in self._candidate_pairs:
            if p["pair_id"] in self._resolutions:
                res = self._resolutions[p["pair_id"]]
                p["status"] = res["status"]
                p["resolution"] = res
        print(f"[✓] DuplicateService indexed {len(self._candidate_pairs)} candidate duplicate/ghost work pairs.")

    def get_duplicates(
        self,
        scope: Optional[Dict[str, Any]] = None,
        min_similarity: float = 70.0,
        status: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Returns list of suspected duplicate pairs with RBAC filtering."""
        results = self._candidate_pairs

        # Multi-Tenant Jurisdiction Filtering
        if scope and scope.get("strict_isolation", True):
            role = scope.get("role")
            if role == "DISTRICT_AUTHORITY":
                u_dist = str(scope.get("IDA_NAME", "")).strip().upper()
                results = [
                    p for p in results if u_dist in p["district_name"].upper() or p["district_name"].upper() in u_dist
                ]
            elif role == "STATE_NODAL_OFFICER":
                u_state = str(scope.get("STATE_NAME", "")).strip().upper()
                results = [p for p in results if p["state_name"].upper() == u_state]
            elif role == "MP_USER":
                u_mp = str(scope.get("MP_NAME", "")).strip().lower()
                results = [
                    p
                    for p in results
                    if u_mp in p["project_a"]["mp_name"].lower() or u_mp in p["project_b"]["mp_name"].lower()
                ]

        if state:
            results = [p for p in results if p["state_name"].upper() == state.upper()]
        if district:
            d_q = str(district).strip().upper()
            results = [p for p in results if d_q in p["district_name"].upper() or p["district_name"].upper() in d_q]
        if min_similarity:
            results = [p for p in results if p["similarity_pct"] >= min_similarity]
        if status:
            results = [p for p in results if p["status"].upper() == status.upper()]

        # Apply any in-memory resolutions
        for p in results:
            if p["pair_id"] in self._resolutions:
                res = self._resolutions[p["pair_id"]]
                p["status"] = res["status"]
                p["resolution"] = res

        return results

    def resolve_duplicate(
        self,
        pair_id: str,
        decision: str,
        user: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Records investigator decision (CONFIRMED_DUPLICATE or MARKED_LEGITIMATE)."""
        res = {
            "pair_id": pair_id,
            "status": decision,
            "resolved_by": user,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._resolutions[pair_id] = res

        # Persist to SQLite database
        from backend.services.audit_service import AuditService

        AuditService.get_instance().save_duplicate_resolution(
            pair_id=pair_id,
            status=decision,
            resolved_by=user,
            notes=notes,
            timestamp=res["timestamp"],
        )

        # Update candidate in list if present
        for p in self._candidate_pairs:
            if p["pair_id"] == pair_id:
                p["status"] = decision
                p["resolution"] = res
                break

        return res
