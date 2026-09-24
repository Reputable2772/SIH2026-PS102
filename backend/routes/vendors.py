"""
Vendor & Contractor Monopoly Matrix Endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.services.data_service import DataService

router = APIRouter(prefix="/vendors", tags=["Vendor & Monopoly Analytics"])


@router.get("", response_model=Dict[str, Any])
def search_vendors(
    query: Optional[str] = Query(None, description="Search by Vendor name"),
    hhi_risk: Optional[str] = Query(None, description="Filter by CONCENTRATED or COMPETITIVE"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    """Returns contractors with market concentration and recurrence risk indicators."""
    ds = DataService.get_instance()
    vendors = ds.vendor_directory

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
def get_vendor_profile(vendor_name: str):
    """Returns vendor work distribution, district spread, and contract history."""
    ds = DataService.get_instance()
    v_info = next((v for v in ds.vendor_directory if v["vendor_name"].lower() == vendor_name.lower()), None)
    if not v_info:
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor_name}' not found.")

    sub = ds.df_works[ds.df_works["primary_vendor"].astype(str).str.lower() == vendor_name.lower()]
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
