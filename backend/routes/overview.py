"""
Overview and Macro Trend API Endpoints.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends

from backend.core.auth import get_tenant_scope
from backend.services.data_service import DataService

router = APIRouter(prefix="/overview", tags=["National Overview & Trends"])


@router.get("", response_model=Dict[str, Any])
def get_platform_overview(scope: Dict[str, Any] = Depends(get_tenant_scope)):
    """Returns high-level KPI cards and priority distribution tailored to active tenant."""
    ds = DataService.get_instance()
    return ds.get_national_overview(scope)


@router.get("/trends", response_model=List[Dict[str, Any]])
def get_macro_trends():
    """Returns longitudinal operational indicators (2020-2026)."""
    ds = DataService.get_instance()
    trends_df = ds.engine.analyze_trends(ds.df_works)
    if trends_df.empty:
        return []
    records = []
    for r in trends_df.to_dict(orient="records"):
        year_str = str(int(r.get("sanction_year", 2024)))
        sanc = float(r.get("total_sanctioned_amount", 0.0))
        disb = float(r.get("total_disbursed", 0.0))
        works_cnt = int(r.get("total_sanctioned_works", 0))
        comp_pct = float(r.get("completion_rate_pct", 0.0))
        records.append({
            "tenure_or_year": year_str,
            "sanction_year": int(year_str) if year_str.isdigit() else 2024,
            "sanctioned_cr": round(sanc / 1e7, 2),
            "disbursed_cr": round(disb / 1e7, 2),
            "total_sanctioned_amount": sanc,
            "total_disbursed": disb,
            "works_count": works_cnt,
            "completion_rate": comp_pct,
            "completion_rate_pct": comp_pct,
            "avg_sanction_delay": float(r.get("avg_sanction_delay", 0.0)),
        })
    return records
