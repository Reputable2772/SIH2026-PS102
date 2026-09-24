"""
Auth and Persona Switching Routes.
"""

from typing import Dict, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.core.auth import DEMO_PERSONAS, UserProfile, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


class LoginRequest(BaseModel):
    persona_id: str


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
def switch_persona(payload: LoginRequest):
    """Generates a signed JWT session token for the selected demo persona."""
    persona_id = payload.persona_id
    if persona_id not in DEMO_PERSONAS:
        persona_id = "central_auditor"

    user = DEMO_PERSONAS[persona_id]
    token = create_access_token({"sub": user.id, "persona_id": persona_id, "role": user.role})
    return LoginResponse(access_token=token, user=user)
