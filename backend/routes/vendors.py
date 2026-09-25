"""
Vendor & Contractor Monopoly Matrix Endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.core.auth import UserRole, get_tenant_scope, redact_vendor_name
from backend.services.data_service import DataService

router = APIRouter(prefix="/vendors", tags=["Vendor & Monopoly Analytics"])


@router.get("", response_model=Dict[str, Any])
def search_vendors(
    query: Optional[str] = Query(None, description="Search by Vendor name"),
    hhi_risk: Optional[str] = Query(None, description="Filter by CONCENTRATED or COMPETITIVE"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Returns contractors with market concentration and recurrence risk indicators, scoped to active tenant."""
    ds = DataService.get_instance()
    vendors = ds.vendor_directory

    # Enforce Tenant Isolation
    if scope.get("strict_isolation", True):
        role = scope.get("role")
        if role == UserRole.DISTRICT_AUTHORITY:
            ida_name = str(scope.get("IDA_NAME", "")).upper()
            active_vendors = ds.get_vendors_for_district(ida_name)
            vendors = [v for v in vendors if v["vendor_name"] in active_vendors]
        elif role == UserRole.STATE_NODAL_OFFICER:
            state_name = str(scope.get("STATE_NAME", "")).upper()
            active_vendors = ds.get_vendors_for_state(state_name)
            vendors = [v for v in vendors if v["vendor_name"] in active_vendors]
        elif role == UserRole.MP_USER:
            mp_name = str(scope.get("MP_NAME", "")).lower()
            sub_works = ds.df_works[ds.df_works["MP_NAME"].astype(str).str.lower().str.contains(mp_name)]
            active_vendors = set(sub_works["primary_vendor"].dropna().unique())
            vendors = [v for v in vendors if v["vendor_name"] in active_vendors]

    # Redaction for public citizens
    can_view_unredacted = scope.get("can_view_unredacted_vendors", True)
    if not can_view_unredacted or scope.get("is_citizen"):
        vendors = [
            {**v, "vendor_name": redact_vendor_name(v["vendor_name"], False)}
            for v in vendors
        ]

    if hhi_risk:
        vendors = [v for v in vendors if v["hhi_risk"].upper() == hhi_risk.upper()]
    if query:
        q = query.lower()
        vendors = [v for v in vendors if q in v["vendor_name"].lower()]

    total = len(vendors)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": vendors[start:end],
    }


@router.get("/{vendor_name}", response_model=Dict[str, Any])
def get_vendor_profile(
    vendor_name: str,
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Returns vendor work distribution, district spread, and contract history, scoped to active tenant."""
    ds = DataService.get_instance()
    v_info = next((v for v in ds.vendor_directory if v["vendor_name"].lower() == vendor_name.lower()), None)
    if not v_info:
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor_name}' not found.")

    # Scoped works
    sub = ds.apply_tenant_filter(
        ds.df_works[ds.df_works["primary_vendor"].astype(str).str.lower() == vendor_name.lower()],
        scope
    )

    if scope.get("strict_isolation", True) and sub.empty:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: Contractor '{vendor_name}' has no active or recorded projects in your jurisdiction.",
        )
    dist_spread = sub["IDA_NAME"].value_counts().head(5).to_dict()

    works = []
    for _, row in sub.head(10).iterrows():
        rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
        works.append({
            "work_rec_id": rec_id,
            "description": str(row.get("WORK_DESCRIPTION", "Project")),
            "state_name": str(row.get("STATE_NAME", "N/A")),
            "ida_name": str(row.get("IDA_NAME", "N/A")),
            "sanction_amount": float(row.get("SANCTION_AMOUNT", 0.0)),
            "total_disbursed": float(row.get("total_disbursed", 0.0)),
            "priority": str(row.get("priority", "LOW")),
        })

    return {
        "profile": v_info,
        "district_distribution": [{"district": k, "works_count": v} for k, v in dist_spread.items()],
        "sample_works": works,
    }
