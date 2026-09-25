"""
AI Priority-Work Recommendations & Draft Letter API Endpoints (Pillars 12, 13, 14).
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.core.auth import UserProfile, get_current_user, get_tenant_scope
from backend.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["AI Priority Recommendations & Draft Letter"])


class GenerateDraftLetterRequest(BaseModel):
    selected_rec_ids: List[str]
    mp_name: Optional[str] = None
    constituency: Optional[str] = None
    district_authority_name: Optional[str] = None


@router.get("", response_model=List[Dict[str, Any]])
def get_recommendations(
    district: Optional[str] = Query(None),
    quota_focus: Optional[str] = Query(None),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Retrieves AI-prioritized project recommendations tailored to local need & quotas."""
    svc = RecommendationService.get_instance()
    return svc.get_recommendations(scope=scope, district=district, quota_focus=quota_focus)


@router.post("/draft-letter", response_model=Dict[str, Any])
def generate_draft_recommendation_letter(
    payload: GenerateDraftLetterRequest,
    user: UserProfile = Depends(get_current_user),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """
    Generates an official Form 2B recommendation letter from Hon'ble MP to District Authority.
    """
    svc = RecommendationService.get_instance()
    mp_name = payload.mp_name or user.name or "Smt. Supriya Sule"
    constituency = payload.constituency or scope.get("CONSTITUENCY") or "Baramati (Maharashtra)"
    dist_name = payload.district_authority_name or scope.get("IDA_NAME") or "Pune District Administration"

    return svc.generate_draft_recommendation_letter(
        selected_rec_ids=payload.selected_rec_ids,
        mp_name=mp_name,
        constituency=constituency,
        district_authority_name=dist_name,
        scope=scope,
    )
