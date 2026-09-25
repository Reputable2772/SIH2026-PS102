"""
Auth and Persona Switching Routes with Dynamic Multi-Tenant Context Support.
"""

import uuid
from typing import Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.core.auth import DEMO_PERSONAS, UserProfile, UserRole, create_access_token, get_current_user
from backend.services.data_service import DataService

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


class SwitchPersonaRequest(BaseModel):
    persona_id: Optional[str] = None
    role: Optional[UserRole] = None
    state: Optional[str] = None
    district: Optional[str] = None
    mp_name: Optional[str] = None
    constituency: Optional[str] = None
    strict_isolation: Optional[bool] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


@router.get("/personas", response_model=Dict[str, UserProfile])
def list_available_personas():
    """Lists pre-configured demo personas representing different government tiers."""
    return DEMO_PERSONAS


@router.get("/me", response_model=UserProfile)
def get_authenticated_user_profile(user: UserProfile = Depends(get_current_user)):
    """Returns currently authenticated user profile and permissions."""
    return user


@router.post("/switch-persona", response_model=LoginResponse)
def switch_persona(payload: SwitchPersonaRequest):
    """
    Generates a signed JWT session token for either a pre-configured demo persona
    or a fully dynamic custom MP, District Authority, or State Officer persona.
    """
    ds = DataService.get_instance()

    # 1. Custom Dynamic Persona Configuration
    if payload.role:
        role = payload.role
        strict = payload.strict_isolation if payload.strict_isolation is not None else True
        user_id = f"usr_{role.value.lower()}_{uuid.uuid4().hex[:6]}"

        if role == UserRole.MP_USER:
            mp_query = (payload.mp_name or "Supriya Sule").strip()
            # Match MP against full directory
            tokens = [t.lower() for t in mp_query.split() if len(t) > 2]
            matched_mp = None
            if tokens:
                matched_mp = next((m for m in ds.mp_directory if all(t in m["mp_name"].lower() for t in tokens)), None)
            if not matched_mp:
                matched_mp = next((m for m in ds.mp_directory if mp_query.lower() in m["mp_name"].lower()), None)

            official_name = matched_mp["mp_name"] if matched_mp else mp_query
            constituency = matched_mp["constituency"] if matched_mp else (payload.constituency or "General")
            state = matched_mp["state_name"] if matched_mp else (payload.state or "All-India")
            house = matched_mp["house"] if matched_mp else "Lok Sabha"

            user = UserProfile(
                id=user_id,
                name=f"Hon. {official_name}",
                email=f"{official_name.lower().replace(' ', '.')}@sansad.nic.in",
                role=UserRole.MP_USER,
                organization=f"Parliament of India ({house})",
                state=state,
                district=payload.district or None,
                constituency=constituency,
                mp_name=official_name,
                permissions=["read_mp_portfolio", "track_recommendations", "download_constituency_summary"],
                strict_isolation=strict,
            )

        elif role == UserRole.DISTRICT_AUTHORITY:
            state = (payload.state or "MAHARASHTRA").upper()
            district = (payload.district or "PUNE").upper()
            user = UserProfile(
                id=user_id,
                name=f"District Magistrate, {district.title()}",
                email=f"collector.{district.lower().replace(' ', '')}@{state.lower().replace(' ', '')}.gov.in",
                role=UserRole.DISTRICT_AUTHORITY,
                organization=f"Office of the District Magistrate & IDA {district.title()}",
                state=state,
                district=district,
                permissions=[
                    "read_district",
                    "dispatch_dqm_inspection",
                    "signoff_milestone",
                    "manage_district_review_queue",
                    "simulate_thresholds",
                ],
                strict_isolation=strict,
            )

        elif role == UserRole.STATE_NODAL_OFFICER:
            state = (payload.state or "MAHARASHTRA").upper()
            user = UserProfile(
                id=user_id,
                name=f"State Nodal Officer ({state.title()})",
                email=f"sno.planning@{state.lower().replace(' ', '')}.gov.in",
                role=UserRole.STATE_NODAL_OFFICER,
                organization=f"Planning Department, Govt. of {state.title()}",
                state=state,
                district=None,
                permissions=[
                    "read_state",
                    "export_state_report",
                    "flag_district",
                    "review_state_works",
                    "simulate_thresholds",
                ],
                strict_isolation=strict,
            )

        elif role == UserRole.CENTRAL_AUDITOR:
            user = UserProfile(
                id=user_id,
                name="Central Auditor (MoSPI / CAG)",
                email="auditor@mospi.gov.in",
                role=UserRole.CENTRAL_AUDITOR,
                organization="MoSPI — Autonomous Analytical Oversight Wing",
                state=None,
                district=None,
                permissions=[
                    "read_all",
                    "export_dossier",
                    "trigger_audit",
                    "admin_config",
                    "view_unredacted_vendors",
                    "simulate_thresholds",
                ],
                strict_isolation=False,
            )

        else:  # CITIZEN
            user = UserProfile(
                id=user_id,
                name="Public Citizen Vigilance",
                email="citizen@public.org.in",
                role=UserRole.CITIZEN,
                organization="Public Governance Transparency",
                state=payload.state or None,
                district=payload.district or None,
                permissions=["read_public_map", "view_public_dossier", "browse_completed_works"],
                strict_isolation=False,
            )

    # 2. Pre-configured Demo Persona Switch
    else:
        persona_id = payload.persona_id or "central_auditor"
        if persona_id not in DEMO_PERSONAS:
            persona_id = "central_auditor"
        base_user = DEMO_PERSONAS[persona_id]
        user = base_user.model_copy()
        if payload.strict_isolation is not None:
            user.strict_isolation = payload.strict_isolation

    # Issue signed JWT with embedded user profile
    token = create_access_token(
        {
            "sub": user.id,
            "persona_id": payload.persona_id or user.role.value.lower(),
            "role": user.role.value,
            "user": user.model_dump(),
        }
    )

    return LoginResponse(access_token=token, user=user)
