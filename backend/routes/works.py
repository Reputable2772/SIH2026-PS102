"""
Works Explorer & Project Search Endpoints.
"""

from typing import Any, Dict, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.core.auth import get_tenant_scope, validate_tenant_query
from backend.services.data_service import DataService

router = APIRouter(prefix="/works", tags=["Canonical Works"])


@router.get("", response_model=Dict[str, Any])
def search_works(
    query: Optional[str] = Query(None, description="Free text search across description, ID, MP, or IDA"),
    state: Optional[str] = Query(None, description="State filter"),
    district: Optional[str] = Query(None, description="District / IDA filter"),
    mp_name: Optional[str] = Query(None, description="MP filter"),
    category: Optional[str] = Query(None, description="Work category filter"),
    priority: Optional[str] = Query(None, description="Priority tier: CRITICAL, HIGH, MEDIUM, LOW"),
    sort_by: Optional[str] = Query(
        None, description="Sort column: priority, sanction_amount, total_disbursed, days_rec_to_sanction, work_rec_id"
    ),
    sort_order: Optional[str] = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Searches and filters across 102k+ canonical projects, automatically scoped to active tenant."""
    # Enforce strict multi-tenant boundary
    validate_tenant_query(scope, state=state, district=district, mp_name=mp_name)

    ds = DataService.get_instance()
    return ds.query_works(
        scope=scope,
        query=query,
        state=state,
        district=district,
        mp_name=mp_name,
        category=category,
        priority=priority,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/{rec_id}", response_model=Dict[str, Any])
def get_work_details(
    rec_id: str,
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Retrieves full record for a specific work with tenant scoping."""
    ds = DataService.get_instance()
    rec_clean = str(rec_id).strip()

    if not ds.verify_work_access(rec_clean, scope):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Work #{rec_clean} is outside your active tenant jurisdiction.",
        )

    match = ds.df_works[ds.df_works["WORK_RECOMMENDATION_DTL_ID"].astype(str) == rec_clean]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Work with recommendation ID '{rec_id}' not found.")
    row = match.iloc[0].to_dict()

    # Redact vendor if viewer lacks unredacted vendor permissions
    from backend.core.auth import redact_vendor_name

    can_view = bool(scope.get("can_view_unredacted_vendors", False))
    if "primary_vendor" in row:
        row["primary_vendor"] = redact_vendor_name(row["primary_vendor"], can_view)

    return {k: (None if pd.isna(v) else v) for k, v in row.items()}
