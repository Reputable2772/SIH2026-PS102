"""
Statutory Compliance Radar API Endpoints (Pillar 11).
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from backend.core.auth import get_tenant_scope, validate_tenant_query
from backend.services.compliance_service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["Statutory Compliance Radar"])


@router.get("", response_model=Dict[str, Any])
def get_compliance_radar(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """
    Evaluates statutory compliance (15% SC, 7.5% ST, Prohibited works, 45-day SLA).
    Applies multi-tenant RBAC isolation.
    """
    validate_tenant_query(scope, state=state, district=district)
    svc = ComplianceService.get_instance()
    return svc.evaluate_compliance(scope=scope, state=state, district=district)
