"""
District & Constituency Intelligence Endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.services.data_service import DataService

router = APIRouter(prefix="/districts", tags=["District & Constituency Intelligence"])


@router.get("", response_model=List[Dict[str, Any]])
def get_all_districts(state: Optional[str] = Query(None, description="Optional State filter")):
    """Returns districts matching the state or all nationwide districts."""
    ds = DataService.get_instance()
    if state:
        return ds.get_districts_for_state(state)
    
    # Return sample top districts nationally
    records = []
    for state_name in list(ds.state_metrics.keys())[:10]:
        records.extend(ds.get_districts_for_state(state_name)[:4])
    return records


@router.get("/{state}/{district}", response_model=Dict[str, Any])
def get_district_deep_dive(state: str, district: str):
    """Returns detailed bottleneck and contractor concentration profile for an IDA."""
    ds = DataService.get_instance()
    d_q = district.strip().upper()
    sub = ds.df_works[
        (ds.df_works["STATE_NAME"].astype(str).str.upper() == state.upper()) &
        (ds.df_works["IDA_NAME"].astype(str).str.upper().apply(lambda v: d_q in v or v in d_q))
    ]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"District '{district}' in '{state}' not found.")

    total_works = len(sub)
    sanc_amt = float(sub["SANCTION_AMOUNT"].sum())
    disb_amt = float(sub["total_disbursed"].sum())
    comp_cnt = int(sub["ACTUAL_END_DATE"].notna().sum()) if "ACTUAL_END_DATE" in sub.columns else 0

    # Top IAs in this district
    top_ias = []
    if "ia_name" in sub.columns:
        ia_counts = sub["ia_name"].value_counts().head(5).to_dict()
        top_ias = [{"ia_name": k, "works_count": v} for k, v in ia_counts.items()]

    # Top Vendors in this district
    top_vendors = []
    if "primary_vendor" in sub.columns:
        v_agg = sub.groupby("primary_vendor")["total_disbursed"].sum().sort_values(ascending=False).head(5).to_dict()
        top_vendors = [{"vendor_name": k, "disbursed_cr": round(v / 1e7, 2)} for k, v in v_agg.items()]

    return {
        "state_name": state.title(),
        "district_name": district.title(),
        "total_works": total_works,
        "sanctioned_amount_cr": round(sanc_amt / 1e7, 2),
        "disbursed_amount_cr": round(disb_amt / 1e7, 2),
        "completed_works": comp_cnt,
        "completion_pct": round((comp_cnt / max(total_works, 1)) * 100, 1),
        "top_implementing_agencies": top_ias,
        "top_vendors": top_vendors,
    }
