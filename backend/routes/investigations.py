"""
Investigation Center & Case Management API Endpoints (Pillars 7, 9, 17, 18).
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.core.auth import UserProfile, get_current_user, get_tenant_scope
from backend.services.investigation_service import InvestigationService

router = APIRouter(prefix="/investigations", tags=["Investigation Center & Case Management"])


class UpdateStageRequest(BaseModel):
    to_stage: str
    notes: str = ""


class AddEvidenceRequest(BaseModel):
    note: str


class CalibrationFeedbackRequest(BaseModel):
    feedback: str  # "CONFIRMED_ANOMALY" | "FALSE_POSITIVE" | "POLICY_EXEMPTION"
    findings: str


@router.get("", response_model=List[Dict[str, Any]])
def list_investigation_cases(
    stage: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Retrieves cases in the investigation pipeline with RBAC jurisdiction filtering."""
    svc = InvestigationService.get_instance()
    return svc.get_cases(scope=scope, stage=stage, priority=priority, search=search)


@router.get("/summary", response_model=Dict[str, Any])
def get_investigation_summary(scope: Dict[str, Any] = Depends(get_tenant_scope)):
    """Returns investigation pipeline KPI aggregates."""
    svc = InvestigationService.get_instance()
    return svc.get_summary_stats(scope=scope)


@router.get("/{case_id}", response_model=Dict[str, Any])
def get_case_detail(
    case_id: str,
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Returns full investigation case detail and historical audit trail."""
    svc = InvestigationService.get_instance()
    try:
        case = svc.get_case_detail(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    # Multi-tenant jurisdiction check
    if scope and scope.get("strict_isolation", True):
        role = scope.get("role")
        if role == "DISTRICT_AUTHORITY":
            u_dist = str(scope.get("IDA_NAME", "")).strip().upper()
            if u_dist not in case["district_name"].upper():
                raise HTTPException(status_code=403, detail="Forbidden: Case is outside your territorial jurisdiction.")
        elif role == "STATE_NODAL_OFFICER":
            u_state = str(scope.get("STATE_NAME", "")).strip().upper()
            if case["state_name"].upper() != u_state:
                raise HTTPException(status_code=403, detail="Forbidden: Case is outside your state jurisdiction.")

    return case


@router.patch("/{case_id}/stage", response_model=Dict[str, Any])
def update_case_stage(
    case_id: str,
    payload: UpdateStageRequest,
    user: UserProfile = Depends(get_current_user),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Transitions case to another stage in the Kanban workflow."""
    svc = InvestigationService.get_instance()
    # Check permission
    required_perms = {"dispatch_dqm_inspection", "manage_district_review_queue", "trigger_audit", "admin_config"}
    if not any(p in user.permissions for p in required_perms):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Role '{user.role}' lacks authority to transition investigation stages.",
        )

    try:
        return svc.update_stage(
            case_id=case_id,
            to_stage=payload.to_stage,
            changed_by=user.name or "Oversight Officer",
            notes=payload.notes,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/{case_id}/notes", response_model=Dict[str, Any])
def add_case_note(
    case_id: str,
    payload: AddEvidenceRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Appends an evidence note or field finding."""
    svc = InvestigationService.get_instance()
    try:
        return svc.add_evidence_note(
            case_id=case_id,
            note_text=payload.note,
            author=user.name or "Investigator",
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")


@router.post("/{case_id}/calibrate", response_model=Dict[str, Any])
def calibrate_model_feedback(
    case_id: str,
    payload: CalibrationFeedbackRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Submits human-in-the-loop calibration feedback to refine AI detector accuracy."""
    svc = InvestigationService.get_instance()
    try:
        return svc.submit_calibration_feedback(
            case_id=case_id,
            feedback=payload.feedback,
            findings=payload.findings,
            author=user.name or "Senior Auditor",
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
