"""
Review Action and Audit Log Endpoints.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.core.auth import UserProfile, get_current_user, get_tenant_scope
from backend.services.audit_service import AuditService
from backend.services.data_service import DataService

router = APIRouter(prefix="/actions", tags=["Review Actions & Audit Trail"])


class UpdateReviewRequest(BaseModel):
    status: str
    checked_actions: List[str]
    auditor_notes: str = ""
    auditor_name: Optional[str] = None


@router.get("/{rec_id}", response_model=Dict[str, Any])
def get_work_review_status(
    rec_id: str,
    user: UserProfile = Depends(get_current_user),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Retrieves saved review state and AC-19 checklist actions for a work with tenant boundary checks."""
    ds = DataService.get_instance()
    rec_clean = str(rec_id).strip()
    if not ds.verify_work_access(rec_clean, scope):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Review file for #{rec_clean} is outside your territorial jurisdiction.",
        )
    svc = AuditService.get_instance()
    return svc.get_review_state(rec_clean)


@router.post("/{rec_id}", response_model=Dict[str, Any])
def update_work_review_status(
    rec_id: str,
    payload: UpdateReviewRequest,
    user: UserProfile = Depends(get_current_user),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Updates review state, checklist items, and auditor notes with RBAC authorization."""
    # 1. Permission check
    required_perms = {"dispatch_dqm_inspection", "manage_district_review_queue", "trigger_audit", "admin_config"}
    if not any(p in user.permissions for p in required_perms):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: User role '{user.role}' lacks authority to update official review actions or sign off checklists.",
        )

    # 2. Status validation
    valid_statuses = {"UNDER_REVIEW", "DQM_DISPATCHED", "RESOLVED", "ESCALATED_TO_CAG"}
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{payload.status}'. Must be one of {valid_statuses}",
        )

    # 3. Tenant jurisdiction check
    ds = DataService.get_instance()
    if not ds.verify_work_access(rec_id, scope):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Work #{rec_id} is outside your active territorial jurisdiction ({scope.get('STATE_NAME') or ''} {scope.get('IDA_NAME') or ''}).",
        )

    # 4. Save review action with authenticated actor
    auditor_label = payload.auditor_name or user.name or "Authorized Officer"
    svc = AuditService.get_instance()
    return svc.save_review_state(
        work_rec_id=rec_id,
        status=payload.status,
        checked_actions=payload.checked_actions,
        auditor_notes=payload.auditor_notes,
        auditor_name=auditor_label,
    )
