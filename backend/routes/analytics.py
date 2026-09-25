"""
Natural Language Analytics Assistant API Endpoints (Pillar 15).
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.core.auth import get_tenant_scope
from backend.services.natural_query_service import NaturalQueryService

router = APIRouter(prefix="/analytics", tags=["Natural-Language Analytics Assistant"])


class QueryRequest(BaseModel):
    query: str
    limit: Optional[int] = 50


@router.post("/query", response_model=Dict[str, Any])
def run_natural_query(
    payload: QueryRequest,
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Translates plain English query into structured analytics filters with RBAC isolation."""
    svc = NaturalQueryService.get_instance()
    return svc.query(
        query_text=payload.query,
        scope=scope,
        limit=payload.limit or 50,
    )


@router.get("/suggestions", response_model=List[str])
def get_query_suggestions():
    """Returns clickable example query prompts."""
    svc = NaturalQueryService.get_instance()
    return svc.get_suggestions()
