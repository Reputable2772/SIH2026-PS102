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
    return trends_df.to_dict(orient="records")
