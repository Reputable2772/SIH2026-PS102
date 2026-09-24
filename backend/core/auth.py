"""
Role-Based Access Control (RBAC) & Multi-Tenant Scoping for MPLADS Platform.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import jwt
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from backend.core.config import ALGORITHM, SECRET_KEY


class UserRole(str, Enum):
    CENTRAL_AUDITOR = "CENTRAL_AUDITOR"  # MoSPI, CAG, Central PMO (National)
    STATE_NODAL_OFFICER = "STATE_NODAL_OFFICER"  # SNO (State Tenant)
    DISTRICT_AUTHORITY = "DISTRICT_AUTHORITY"  # IDA / District Magistrate (District Tenant)
    MP_USER = "MP_USER"  # Member of Parliament (Constituency Tenant)
    CITIZEN = "CITIZEN"  # Public Citizen (Read-only National Summary)


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    organization: str
    state: Optional[str] = None
    district: Optional[str] = None
    constituency: Optional[str] = None
    mp_name: Optional[str] = None
    permissions: List[str]


# Pre-configured demo personas for fast switching in UI
DEMO_PERSONAS: Dict[str, UserProfile] = {
    "central_auditor": UserProfile(
        id="usr_central_01",
        name="Dr. Rajesh Verma",
        email="rajesh.verma@mospi.gov.in",
        role=UserRole.CENTRAL_AUDITOR,
        organization="MoSPI — Autonomous Analytical Oversight Wing",
        state=None,
        district=None,
        permissions=["read_all", "export_dossier", "trigger_audit", "admin_config", "view_unredacted_vendors"],
    ),
    "state_nodal_officer": UserProfile(
        id="usr_sno_mh",
        name="Priya Deshmukh, IAS",
        email="sno.planning@maharashtra.gov.in",
        role=UserRole.STATE_NODAL_OFFICER,
        organization="Planning Department, Govt. of Maharashtra",
        state="MAHARASHTRA",
        district=None,
        permissions=["read_state", "export_state_report", "flag_district", "review_state_works"],
    ),
    "district_authority": UserProfile(
        id="usr_ida_pune",
        name="District Magistrate, Pune",
        email="collector.pune@maharashtra.gov.in",
        role=UserRole.DISTRICT_AUTHORITY,
        organization="Office of the District Magistrate & IDA Pune",
        state="MAHARASHTRA",
        district="PUNE",
        permissions=["read_district", "dispatch_dqm_inspection", "signoff_milestone", "manage_district_review_queue"],
    ),
    "mp_user": UserProfile(
        id="usr_mp_baramati",
        name="Hon. Supriya Sule",
        email="mp.baramati@sansad.nic.in",
        role=UserRole.MP_USER,
        organization="Parliament of India (Lok Sabha)",
        state="MAHARASHTRA",
        district="PUNE",
        constituency="Baramati",
        mp_name="Supriya Sule",
        permissions=["read_mp_portfolio", "track_recommendations", "download_constituency_summary"],
    ),
    "citizen": UserProfile(
        id="usr_citizen_pub",
        name="Citizen Vigilance",
        email="citizen@public.org.in",
        role=UserRole.CITIZEN,
        organization="Public Governance Transparency",
        state=None,
        district=None,
        permissions=["read_public_map", "view_public_dossier", "browse_completed_works"],
    ),
}


GUEST_CITIZEN = UserProfile(
    id="usr_guest",
    name="Public Guest",
    email="guest@public.gov.in",
    role=UserRole.CITIZEN,
    organization="Public Citizen Transparency Portal",
    state=None,
    district=None,
    permissions=["read_public_map", "view_public_dossier", "browse_completed_works"],
)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    authorization: Optional[str] = Header(None),
    x_persona_id: Optional[str] = Header(None),
) -> UserProfile:
    """
    Resolves the current user either from direct X-Persona-Id header
    or JWT Authorization header. Falls back to unauthenticated GUEST_CITIZEN.
    """
    if x_persona_id and x_persona_id in DEMO_PERSONAS:
        return DEMO_PERSONAS[x_persona_id]

    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = decode_access_token(token)
        persona_id = payload.get("persona_id")
        if persona_id and persona_id in DEMO_PERSONAS:
            return DEMO_PERSONAS[persona_id]

    # Non-authenticated requests safely default to public guest citizen
    return GUEST_CITIZEN


def require_permission(permission: str):
    """Dependency that enforces a specific permission on the authenticated user."""
    def permission_checker(user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires permission '{permission}'. Role '{user.role}' lacks this permission.",
            )
        return user
    return permission_checker


def require_any_permission(*permissions: str):
    """Dependency that enforces at least one of the listed permissions."""
    def permission_checker(user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if not any(p in user.permissions for p in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of {list(permissions)}. Role '{user.role}' is not authorized.",
            )
        return user
    return permission_checker


def redact_vendor_name(vendor_name: Any, can_view_unredacted: bool) -> str:
    """Masks contractor identity for public or unauthorized viewers."""
    if not vendor_name or str(vendor_name).strip() in ("N/A", "nan", "None", ""):
        return "N/A"
    v = str(vendor_name).strip()
    if can_view_unredacted:
        return v
    if len(v) <= 6:
        return "CONTR-***"
    return f"{v[:3]}***-{v[-4:]}"


def get_tenant_scope(user: UserProfile = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Returns data filter boundaries corresponding to the active tenant role.
    Used by data services to enforce geographic and portfolio isolation.
    """
    scope: Dict[str, Any] = {
        "role": user.role,
        "user_id": user.id,
        "permissions": user.permissions,
        "can_view_unredacted_vendors": "view_unredacted_vendors" in user.permissions,
        "is_citizen": user.role == UserRole.CITIZEN,
    }

    if user.role == UserRole.STATE_NODAL_OFFICER and user.state:
        scope["STATE_NAME"] = user.state.upper()
    elif user.role == UserRole.DISTRICT_AUTHORITY:
        if user.state:
            scope["STATE_NAME"] = user.state.upper()
        if user.district:
            scope["IDA_NAME"] = user.district.upper()
    elif user.role == UserRole.MP_USER and user.mp_name:
        scope["MP_NAME"] = user.mp_name

    return scope
