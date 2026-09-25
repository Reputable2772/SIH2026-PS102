"""
Members of Parliament (MP) Portfolio & Allocation Analytics Endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.core.auth import UserRole, get_tenant_scope, validate_tenant_query
from backend.services.data_service import DataService

router = APIRouter(prefix="/mps", tags=["MP Intelligence"])


@router.get("", response_model=Dict[str, Any])
def search_mps(
    query: Optional[str] = Query(None, description="Search by MP name or constituency"),
    house: Optional[str] = Query(None, description="Filter by LOK_SABHA or RAJYA_SABHA"),
    state: Optional[str] = Query(None, description="Filter by State"),
    risk_tier: Optional[str] = Query(None, description="Filter by risk tier: CRITICAL, HIGH, NORMAL"),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Returns paginated and searchable directory of MPs, strictly scoped to active tenant jurisdiction."""
    validate_tenant_query(scope, state=state)
    ds = DataService.get_instance()
    mps = ds.mp_directory

    # Enforce Role-Based Scoping
    if scope.get("strict_isolation", True):
        role = scope.get("role")
        if role == UserRole.DISTRICT_AUTHORITY:
            # Only MPs whose projects are executed within this district
            ida_name = str(scope.get("IDA_NAME", "")).upper()
            district_mps = ds.get_mps_for_district(ida_name)
            mps = [m for m in mps if m["mp_name"] in district_mps]
        elif role == UserRole.MP_USER:
            user_mp = str(scope.get("MP_NAME", "")).lower()
            mps = [m for m in mps if user_mp in m["mp_name"].lower()]
        elif role == UserRole.STATE_NODAL_OFFICER:
            user_state = str(scope.get("STATE_NAME", "")).upper()
            mps = [m for m in mps if m["state_name"].upper() == user_state]

    if house:
        h_norm = house.upper().replace(" ", "_")
        mps = [m for m in mps if m["house"].upper().replace(" ", "_") == h_norm]
    if state:
        mps = [m for m in mps if m["state_name"].upper() == state.upper()]
    if risk_tier:
        mps = [m for m in mps if m["risk_tier"].upper() == risk_tier.upper()]
    if query:
        q = query.lower()
        mps = [
            m for m in mps
            if q in m["mp_name"].lower() or q in m["constituency"].lower() or q in m["state_name"].lower()
        ]

    total = len(mps)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": mps[start:end],
    }


@router.get("/{mp_name}", response_model=Dict[str, Any])
def get_mp_detail(
    mp_name: str,
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Returns deep-dive portfolio metrics and recommended works for an MP, scoped to active tenant."""
    ds = DataService.get_instance()
    target_mp = next((m for m in ds.mp_directory if m["mp_name"].lower() == mp_name.lower()), None)

    if not target_mp:
        # Fallback partial match
        target_mp = next((m for m in ds.mp_directory if mp_name.lower() in m["mp_name"].lower()), None)

    if not target_mp:
        # Fallback multi-token match (e.g. Supriya Sule matches Smt Supriya Sadanand Sule)
        tokens = [t.lower() for t in mp_name.split() if len(t) > 2]
        if tokens:
            target_mp = next((m for m in ds.mp_directory if all(t in m["mp_name"].lower() for t in tokens)), None)

    if not target_mp:
        raise HTTPException(status_code=404, detail=f"MP '{mp_name}' not found.")

    if scope.get("strict_isolation", True):
        role = scope.get("role")
        if role == UserRole.MP_USER:
            user_mp = str(scope.get("MP_NAME", "")).lower()
            if user_mp not in target_mp["mp_name"].lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access Denied: You are only authorized to inspect your own MP portfolio ({user_mp}).",
                )
        elif role == UserRole.STATE_NODAL_OFFICER:
            user_state = str(scope.get("STATE_NAME", "")).upper()
            if target_mp["state_name"].upper() != user_state:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access Denied: MP belongs to state '{target_mp['state_name']}', outside your state jurisdiction.",
                )

    # Get works recommended by this MP, scoped to tenant
    works_sub = ds.apply_tenant_filter(
        ds.df_works[ds.df_works["MP_NAME"].astype(str).str.lower() == target_mp["mp_name"].lower()],
        scope
    )
    
    categories = works_sub["WORK_CATEGORY"].value_counts().head(6).to_dict()
    recent_works = []
    for _, row in works_sub.head(15).iterrows():
        rec_id = str(row["WORK_RECOMMENDATION_DTL_ID"])
        recent_works.append({
            "work_rec_id": rec_id,
            "description": str(row.get("WORK_DESCRIPTION", "Project")),
            "category": str(row.get("WORK_CATEGORY", "General")),
            "sanction_amount": float(row.get("SANCTION_AMOUNT", 0.0)),
            "total_disbursed": float(row.get("total_disbursed", 0.0)),
            "priority": str(row.get("priority", "LOW")),
            "days_rec_to_sanction": int(row.get("days_rec_to_sanction", 0)),
        })

    return {
        "profile": target_mp,
        "category_distribution": [{"name": k, "count": v} for k, v in categories.items()],
        "sample_works": recent_works,
    }
