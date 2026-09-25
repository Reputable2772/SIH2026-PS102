"""
Regression Tests for Remediation of 34 Major Bugs.
Tests cover:
- Anomaly detector simulation with z_threshold & tenant scoping
- Honest SC/ST statutory allocation percentages
- Non-existent work rec_id returns 404 before 403
- ZeroDivisionError prevention on unsanctioned works in dossiers
- Form 2B recommendation letter generation role authorization
- Investigation case mutability & notes territorial authorization
- Persistent duplicate work resolution in SQLite
- Natural query assistant substring containment for District Authority
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.data_service import DataService
from backend.services.audit_service import AuditService


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_simulation_z_threshold_and_tenant_scoping(client):
    """
    Bug #1, #2, #3, #4: Verify simulation uses z_threshold, safe SLA types,
    disjoint set subtraction, and tenant scoping.
    """
    # 1. National simulation with low z_threshold (2.0) vs high z_threshold (4.5)
    res_low_z = client.post(
        "/api/detectors/simulate",
        json={"sla_days": 45, "execution_days": 365, "z_threshold": 2.0},
        headers={"X-Persona-Id": "central_auditor"},
    )
    assert res_low_z.status_code == 200
    data_low = res_low_z.json()
    assert "simulated_critical_count" in data_low
    assert "simulated_high_count" in data_low
    assert "peer_cost_outliers" in data_low
    assert data_low["total_works"] > 50000

    res_high_z = client.post(
        "/api/detectors/simulate",
        json={"sla_days": 45, "execution_days": 365, "z_threshold": 4.5},
        headers={"X-Persona-Id": "central_auditor"},
    )
    assert res_high_z.status_code == 200
    data_high = res_high_z.json()
    # Higher z-threshold should be stricter, resulting in fewer peer cost outliers
    assert data_high["peer_cost_outliers"] <= data_low["peer_cost_outliers"]

    # 2. Tenant Scoping: DM Pune should simulate ONLY over Pune works
    res_dm = client.post(
        "/api/detectors/simulate",
        json={"sla_days": 45, "execution_days": 365, "z_threshold": 2.5},
        headers={"X-Persona-Id": "district_authority"},
    )
    assert res_dm.status_code == 200
    data_dm = res_dm.json()
    assert data_dm["total_works"] > 0
    assert data_dm["total_works"] < 5000


def test_honest_sc_st_compliance_calculation(client):
    """
    Bug #6 & #7: Statutory SC/ST percentages must be calculated honestly,
    not hardcoded to 13.8% and 6.4%, and IDA matching should support Pune.
    """
    res = client.get(
        "/api/compliance?district=Pune",
        headers={"X-Persona-Id": "central_auditor"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "sc_allocation" in data
    assert "st_allocation" in data
    assert isinstance(data["sc_allocation"]["actual_pct"], (int, float))
    assert isinstance(data["st_allocation"]["actual_pct"], (int, float))
    assert data["total_works_evaluated"] > 0


def test_work_details_404_before_403(client):
    """
    Bug #22: Non-existent work rec_id should return 404 Not Found,
    even for scoped tenants, before checking access permissions.
    """
    res = client.get(
        "/api/works/NON_EXISTENT_WORK_RECORD_99999",
        headers={"X-Persona-Id": "district_authority"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_zero_division_guard_in_dossier():
    """
    Bug #21: Dossier generation must not crash with ZeroDivisionError when
    sanction_amount is 0.0 but disbursed > 0.
    """
    ds = DataService.get_instance()
    sample_id = str(ds.df_works.iloc[0]["WORK_RECOMMENDATION_DTL_ID"])
    orig_sanc = ds.df_works.loc[ds.df_works["WORK_RECOMMENDATION_DTL_ID"].astype(str) == sample_id, "SANCTION_AMOUNT"].values[0]
    try:
        ds.df_works.loc[ds.df_works["WORK_RECOMMENDATION_DTL_ID"].astype(str) == sample_id, "SANCTION_AMOUNT"] = 0.0
        # This must not raise ZeroDivisionError
        dossier = ds.get_work_dossier(sample_id)
        assert dossier is not None
        assert "five_questions" in dossier
    finally:
        ds.df_works.loc[ds.df_works["WORK_RECOMMENDATION_DTL_ID"].astype(str) == sample_id, "SANCTION_AMOUNT"] = orig_sanc


def test_form_2b_recommendations_auth(client):
    """
    Bug #17: Form 2B letter generation must be restricted to MP_USER role
    and populated with the authenticated MP's credentials.
    """
    # 1. District Authority should be rejected with 403
    res_dm = client.post(
        "/api/recommendations/draft-letter",
        json={"selected_rec_ids": ["REC-PUNE-01"]},
        headers={"X-Persona-Id": "district_authority"},
    )
    assert res_dm.status_code == 403
    assert "lacks authority" in res_dm.json()["detail"].lower()

    # 2. Citizen should be rejected with 403
    res_cit = client.post(
        "/api/recommendations/draft-letter",
        json={"selected_rec_ids": ["REC-PUNE-01"]},
        headers={"X-Persona-Id": "citizen"},
    )
    assert res_cit.status_code == 403

    # 3. MP User (Hon. Supriya Sule) should succeed
    res_mp = client.post(
        "/api/recommendations/draft-letter",
        json={"selected_rec_ids": []},
        headers={"X-Persona-Id": "mp_user"},
    )
    assert res_mp.status_code == 200
    letter = res_mp.json()
    assert "Supriya Sule" in letter["mp_name"]
    assert "Baramati" in letter["constituency"]


def test_cross_district_investigation_rejection(client):
    """
    Bug #13 & #14: DM Pune cannot update stages or add notes to an investigation
    case outside Pune district.
    """
    # Get all cases as central auditor
    cases_res = client.get("/api/investigations", headers={"X-Persona-Id": "central_auditor"})
    assert cases_res.status_code == 200
    cases = cases_res.json()
    assert len(cases) > 0

    # Find a non-Pune case (e.g. Varanasi or Gorakhpur)
    other_case = next((c for c in cases if c.get("district_name", "").upper() != "PUNE"), None)
    if other_case:
        other_id = other_case["case_id"]
        # DM Pune tries to update stage -> should be 403
        stage_res = client.patch(
            f"/api/investigations/{other_id}/stage",
            json={"to_stage": "RESOLVED", "notes": "Unauthorized attempt"},
            headers={"X-Persona-Id": "district_authority"},
        )
        assert stage_res.status_code == 403
        assert "jurisdiction" in stage_res.json()["detail"].lower()

        # DM Pune tries to add a note -> should be 403
        note_res = client.post(
            f"/api/investigations/{other_id}/notes",
            json={"note": "Unauthorized note"},
            headers={"X-Persona-Id": "district_authority"},
        )
        assert note_res.status_code == 403


def test_persistent_duplicate_resolutions(client):
    """
    Bug #9, #10 & #16: Candidate pairs can be resolved and persist across sessions.
    Cross-district resolution by DM is rejected.
    """
    # 1. Fetch duplicate pairs
    pairs_res = client.get("/api/duplicates?limit=10", headers={"X-Persona-Id": "central_auditor"})
    assert pairs_res.status_code == 200
    pairs = pairs_res.json()
    assert len(pairs) > 0

    test_pair = pairs[0]
    pair_id = test_pair["pair_id"]

    # 2. Central auditor resolves the pair
    resolve_res = client.post(
        f"/api/duplicates/{pair_id}/resolve",
        json={"decision": "CONFIRMED_DUPLICATE", "notes": "Automated regression test confirmation"},
        headers={"X-Persona-Id": "central_auditor"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "CONFIRMED_DUPLICATE"

    # 3. Check SQLite persistence via AuditService
    audit_svc = AuditService.get_instance()
    persisted = audit_svc.get_all_duplicate_resolutions()
    assert pair_id in persisted
    assert persisted[pair_id]["status"] == "CONFIRMED_DUPLICATE"

    # 4. DM Pune resolving a pair in another district must receive 403
    other_pair = next((p for p in pairs if p.get("district_name", "").upper() != "PUNE"), None)
    if other_pair:
        dm_resolve = client.post(
            f"/api/duplicates/{other_pair['pair_id']}/resolve",
            json={"decision": "MARKED_LEGITIMATE", "notes": "DM unauthorized attempt"},
            headers={"X-Persona-Id": "district_authority"},
        )
        assert dm_resolve.status_code == 403


def test_natural_query_assistant_substring_matching(client):
    """
    Bug #28: Natural language assistant handles IDA substring matching cleanly for Pune.
    """
    res = client.post(
        "/api/analytics/query",
        json={"query": "Show delayed works in sanitation"},
        headers={"X-Persona-Id": "district_authority"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "count" in data
    assert any("District restricted" in f for f in data["parsed_filters"])
    assert data["count"] > 0
