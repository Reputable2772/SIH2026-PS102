"""
Duplicate & Ghost Work Detection Endpoints (Pillar 4).
Allows forensic comparison of suspected duplicate project pairs side-by-side.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.core.auth import UserProfile, get_current_user, get_tenant_scope
from backend.services.audit_service import AuditService
from backend.services.duplicate_service import DuplicateService

router = APIRouter(prefix="/duplicates", tags=["Duplicate & Ghost Work Detection"])


class ResolveDuplicateRequest(BaseModel):
    decision: str  # "CONFIRMED_DUPLICATE" or "MARKED_LEGITIMATE"
    notes: str = ""


@router.get("", response_model=List[Dict[str, Any]])
def list_duplicates(
    min_similarity: float = Query(70.0, ge=0.0, le=100.0),
    status: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """
    Returns suspected duplicate and ghost work pairs with multi-tenant RBAC isolation.
    """
    svc = DuplicateService.get_instance()
    results = svc.get_duplicates(
        scope=scope,
        min_similarity=min_similarity,
        status=status,
        state=state,
        district=district,
    )
    return results[:limit]


@router.get("/stats", response_model=Dict[str, Any])
def duplicate_stats(scope: Dict[str, Any] = Depends(get_tenant_scope)):
    """Returns aggregated summary statistics for detected duplicate works."""
    svc = DuplicateService.get_instance()
    pairs = svc.get_duplicates(scope=scope, min_similarity=0.0)

    total_suspected = len(pairs)
    confirmed = sum(1 for p in pairs if p.get("status") == "CONFIRMED_DUPLICATE")
    legitimate = sum(1 for p in pairs if p.get("status") == "MARKED_LEGITIMATE")
    pending = total_suspected - confirmed - legitimate

    # Potential duplicate funds at risk (sum of lower duplicate sanction amounts)
    potential_risk_funds = sum(
        min(p["project_a"]["sanction_amount"], p["project_b"]["sanction_amount"])
        for p in pairs
        if p.get("status") != "MARKED_LEGITIMATE"
    )

    return {
        "total_pairs_flagged": total_suspected,
        "pending_review": pending,
        "confirmed_duplicates": confirmed,
        "marked_legitimate": legitimate,
        "potential_duplicate_funds_at_risk": round(potential_risk_funds, 2),
        "high_confidence_count": sum(1 for p in pairs if p["similarity_pct"] >= 85.0),
    }


@router.post("/{pair_id}/resolve", response_model=Dict[str, Any])
def resolve_duplicate_pair(
    pair_id: str,
    payload: ResolveDuplicateRequest,
    user: UserProfile = Depends(get_current_user),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """
    Records investigator resolution for a suspected duplicate pair.
    """
    valid_decisions = {"CONFIRMED_DUPLICATE", "MARKED_LEGITIMATE"}
    if payload.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision '{payload.decision}'. Must be one of {valid_decisions}",
        )

    required_perms = {"manage_district_review_queue", "trigger_audit", "admin_config"}
    if not any(p in user.permissions for p in required_perms):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Role '{user.role}' lacks authority to adjudicate duplicate investigations.",
        )

    svc = DuplicateService.get_instance()
    res = svc.resolve_duplicate(
        pair_id=pair_id,
        decision=payload.decision,
        user=user.name or "Authorized Investigator",
        notes=payload.notes,
    )

    # Log to persistent audit store
    audit_svc = AuditService.get_instance()
    with audit_svc._get_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_activity_log (work_rec_id, action_type, details, actor_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                pair_id,
                f"DUPLICATE_{payload.decision}",
                f"Investigation outcome: {payload.decision}. Notes: {payload.notes}",
                user.name or "Investigator",
                res["timestamp"],
            ),
        )
        conn.commit()

    return res
