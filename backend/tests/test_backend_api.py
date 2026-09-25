"""
Comprehensive API Tests for MPLADS Backend.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"


def test_auth_personas(client):
    response = client.get("/api/auth/personas")
    assert response.status_code == 200
    personas = response.json()
    assert "central_auditor" in personas
    assert "district_authority" in personas

    # Test switch persona
    switch_res = client.post("/api/auth/switch-persona", json={"persona_id": "central_auditor"})
    assert switch_res.status_code == 200
    token_data = switch_res.json()
    assert "access_token" in token_data
    assert token_data["user"]["role"] == "CENTRAL_AUDITOR"


def test_overview_endpoints(client):
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_works" in data
    assert data["total_works"] > 0
    assert "total_sanctioned_cr" in data
    assert "priority_summary" in data

    # Test trends
    trends_res = client.get("/api/overview/trends")
    assert trends_res.status_code == 200
    assert isinstance(trends_res.json(), list)


def test_map_endpoints(client):
    response = client.get("/api/map/states")
    assert response.status_code == 200
    states = response.json()
    assert len(states) > 0
    first_state = states[0]["state_name"]

    # Test districts for state
    dist_res = client.get(f"/api/map/districts?state={first_state}")
    assert dist_res.status_code == 200

    # Test GeoJSON endpoint
    geo_res = client.get("/api/map/geojson")
    assert geo_res.status_code == 200
    assert "features" in geo_res.json()


def test_works_search_and_detail(client):
    response = client.get("/api/works?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) == 10

    sample_work = data["items"][0]
    rec_id = sample_work["work_rec_id"]

    detail_res = client.get(f"/api/works/{rec_id}")
    assert detail_res.status_code == 200
    assert str(detail_res.json()["WORK_RECOMMENDATION_DTL_ID"]) == str(rec_id)


def test_dossier_and_html(client):
    # Find a work ID
    works_res = client.get("/api/works?page=1&page_size=5")
    sample_work = works_res.json()["items"][0]
    rec_id = sample_work["work_rec_id"]

    response = client.get(f"/api/dossier/{rec_id}")
    assert response.status_code == 200
    dossier = response.json()
    assert "five_questions" in dossier
    assert "q1_what_happened" in dossier["five_questions"]
    assert "next_review_actions" in dossier

    # Test HTML export
    html_res = client.get(f"/api/dossier/{rec_id}/html")
    assert html_res.status_code == 200
    assert "Governance Dossier" in html_res.text


def test_detectors_and_simulation(client):
    response = client.get("/api/detectors")
    assert response.status_code == 200
    detectors = response.json()
    assert len(detectors) >= 10
    codes = [d["code"] for d in detectors]
    assert "COMP-D1" in codes
    assert "FIN-D6" in codes

    # 1. Unauthenticated / Citizen simulation attempt must be forbidden (403)
    unauth_sim = client.post(
        "/api/detectors/simulate",
        json={"sla_days": 30, "execution_days": 300, "z_threshold": 2.0},
    )
    assert unauth_sim.status_code == 403

    # 2. Authorized Central Auditor simulation succeeds (200)
    auth_sim = client.post(
        "/api/detectors/simulate",
        headers={"X-Persona-Id": "central_auditor"},
        json={"sla_days": 30, "execution_days": 300, "z_threshold": 2.0},
    )
    assert auth_sim.status_code == 200
    sim_data = auth_sim.json()
    assert "total_works" in sim_data
    assert "sanction_sla_breaches" in sim_data


def test_mps_and_vendors(client):
    mps_res = client.get("/api/mps?page=1&page_size=10")
    assert mps_res.status_code == 200
    mps_data = mps_res.json()
    assert mps_data["total"] > 0

    vendors_res = client.get("/api/vendors?page=1&page_size=10")
    assert vendors_res.status_code == 200


def test_audit_actions_sqlite_persistence(client):
    import uuid

    test_rec_id = f"test_work_{uuid.uuid4().hex[:8]}"

    # 1. Unauthenticated or Citizen update attempt is blocked (403 Forbidden)
    forbidden_res = client.post(
        f"/api/actions/{test_rec_id}",
        json={
            "status": "DQM_DISPATCHED",
            "checked_actions": ["Dispatch District Quality Monitor (DQM) for inspection."],
        },
    )
    assert forbidden_res.status_code == 403

    # 2. Authorized Central Auditor update succeeds (200)
    update_res = client.post(
        f"/api/actions/{test_rec_id}",
        headers={"X-Persona-Id": "central_auditor"},
        json={
            "status": "DQM_DISPATCHED",
            "checked_actions": ["Dispatch District Quality Monitor (DQM) for inspection."],
            "auditor_notes": "Urgent site inspection ordered by SNO.",
            "auditor_name": "Priya Deshmukh, IAS",
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["status"] == "DQM_DISPATCHED"
    assert len(updated["checked_actions"]) == 1

    # 3. Fetch again to verify SQLite persistence
    verify_res = client.get(f"/api/actions/{test_rec_id}")
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "DQM_DISPATCHED"
    assert verify_res.json()["auditor_name"] == "Priya Deshmukh, IAS"


def test_rbac_vendor_redaction_and_tenant_scoping(client):
    # Search works as Citizen (vendors should be redacted)
    citizen_res = client.get("/api/works?page=1&page_size=5", headers={"X-Persona-Id": "citizen"})
    assert citizen_res.status_code == 200
    citizen_items = citizen_res.json()["items"]
    for item in citizen_items:
        v = item.get("primary_vendor", "")
        if v not in ("N/A", "None", ""):
            assert "***" in v or v == "N/A"

    # Search works as Central Auditor (vendors unredacted)
    auditor_res = client.get("/api/works?page=1&page_size=5", headers={"X-Persona-Id": "central_auditor"})
    assert auditor_res.status_code == 200


def test_pune_ida_and_baramati_mp_tenant_access(client):
    # Pune IDA has access to Pune works and can view dossier
    pune_works = client.get("/api/works", headers={"X-Persona-Id": "district_authority"}).json()
    assert pune_works["total"] >= 100
    pune_rec_id = pune_works["items"][0]["work_rec_id"]
    pune_dossier = client.get(f"/api/dossier/{pune_rec_id}", headers={"X-Persona-Id": "district_authority"})
    assert pune_dossier.status_code == 200

    # Baramati MP has access to their works and can view dossier
    mp_works = client.get("/api/works", headers={"X-Persona-Id": "mp_user"}).json()
    assert mp_works["total"] >= 30
    mp_rec_id = mp_works["items"][0]["work_rec_id"]
    mp_dossier = client.get(f"/api/dossier/{mp_rec_id}", headers={"X-Persona-Id": "mp_user"})
    assert mp_dossier.status_code == 200

    # Out-of-tenant boundary check: MP cannot access Pune IDA work recommended by another MP
    other_work_rec = "137790"  # recommended by Amol Kolhe
    unauth_dossier = client.get(f"/api/dossier/{other_work_rec}", headers={"X-Persona-Id": "mp_user"})
    assert unauth_dossier.status_code == 403


def test_dynamic_persona_switching_any_mp_and_district(client):
    # Dynamic MP: Switch to Narendra Modi
    switch_modi = client.post("/api/auth/switch-persona", json={"role": "MP_USER", "mp_name": "Narendra Modi"})
    assert switch_modi.status_code == 200
    modi_data = switch_modi.json()
    assert "access_token" in modi_data
    assert modi_data["user"]["constituency"] == "VARANASI"
    token = modi_data["access_token"]

    modi_works = client.get("/api/works", headers={"Authorization": f"Bearer {token}"})
    assert modi_works.status_code == 200
    assert modi_works.json()["total"] > 100

    # Dynamic District: Switch to Varanasi IDA
    switch_dist = client.post(
        "/api/auth/switch-persona",
        json={"role": "DISTRICT_AUTHORITY", "state": "UTTAR PRADESH", "district": "VARANASI"},
    )
    assert switch_dist.status_code == 200
    assert switch_dist.json()["user"]["district"] == "VARANASI"


def test_district_authority_can_simulate_detectors(client):
    res = client.post(
        "/api/detectors/simulate",
        headers={"X-Persona-Id": "district_authority"},
        json={"sla_days": 45, "execution_days": 365, "z_threshold": 2.5},
    )
    assert res.status_code == 200
    data = res.json()
    assert "sanction_sla_breaches" in data


def test_strict_cross_district_prevention_and_entity_scoping(client):
    # DM Pune should receive 403 when querying cross-district or cross-state
    cross_dist = client.get(
        "/api/works?district=THANE",
        headers={"X-Persona-Id": "district_authority"},
    )
    assert cross_dist.status_code == 403
    assert "cross-district" in cross_dist.json()["detail"].lower()

    cross_state = client.get(
        "/api/works?state=KARNATAKA",
        headers={"X-Persona-Id": "district_authority"},
    )
    assert cross_state.status_code == 403

    # Scoped MPs: DM Pune receives only MPs with works in Pune
    scoped_mps = client.get(
        "/api/mps",
        headers={"X-Persona-Id": "district_authority"},
    )
    assert scoped_mps.status_code == 200
    assert scoped_mps.json()["total"] < 50  # Scoped to Pune, far less than 775 national MPs

    # Scoped Vendors: DM Pune receives only contractors with works in Pune
    scoped_v = client.get(
        "/api/vendors",
        headers={"X-Persona-Id": "district_authority"},
    )
    assert scoped_v.status_code == 200
    assert scoped_v.json()["total"] < 200  # Scoped to Pune, far less than 17,773 national vendors


def test_strict_district_and_map_cross_tenant_blocking_and_soi_map(client):
    # 1. DM Pune calling /api/districts should only receive their assigned district
    dist_res = client.get("/api/districts", headers={"X-Persona-Id": "district_authority"})
    assert dist_res.status_code == 200
    dists = dist_res.json()
    assert len(dists) == 1
    assert "pune" in dists[0]["district_name"].lower()

    # 2. DM Pune calling deep dive for another state/district must be blocked with 403
    leak_dive = client.get(
        "/api/districts/Karnataka/Bengaluru",
        headers={"X-Persona-Id": "district_authority"},
    )
    assert leak_dive.status_code == 403
    assert (
        "strictly prohibited" in leak_dive.json()["detail"].lower()
        or "access denied" in leak_dive.json()["detail"].lower()
    )

    # 3. DM Pune calling /api/map/districts?state=Karnataka must be blocked with 403
    map_dist_dm = client.get(
        "/api/map/districts?state=Karnataka",
        headers={"X-Persona-Id": "district_authority"},
    )
    assert map_dist_dm.status_code == 403

    # 4. SNO Maharashtra calling /api/map/districts?state=Karnataka must be blocked with 403
    map_dist_sno = client.get(
        "/api/map/districts?state=Karnataka",
        headers={"X-Persona-Id": "state_nodal_officer"},
    )
    assert map_dist_sno.status_code == 403

    # 5. Central Auditor has national privileges across all districts and map indicators
    auditor_dist = client.get(
        "/api/map/districts?state=Karnataka",
        headers={"X-Persona-Id": "central_auditor"},
    )
    assert auditor_dist.status_code == 200
    assert len(auditor_dist.json()) > 0

    # 6. Verify Survey of India boundaries in GeoJSON
    gj_res = client.get("/api/map/geojson")
    assert gj_res.status_code == 200
    gj_data = gj_res.json()
    assert len(gj_data["features"]) == 36
    names = [f["properties"].get("NAME_1") for f in gj_data["features"]]
    assert "Ladakh" in names
    assert "Jammu and Kashmir" in names

    # Verify northern crown latitude reaches official Survey of India boundary (>= 37.0 N)
    ladakh_feat = [f for f in gj_data["features"] if f["properties"].get("NAME_1") == "Ladakh"][0]
    coords = ladakh_feat["geometry"]["coordinates"]

    def extract_lats(c):
        if isinstance(c[0], (int, float)):
            return [c[1]]
        lat_list = []
        for item in c:
            lat_list.extend(extract_lats(item))
        return lat_list

    lats = extract_lats(coords)
    assert max(lats) > 37.0, f"Ladakh northern boundary must reach sovereign Karakoram/Pamir line, got {max(lats)}"


def test_sno_dm_mp_cross_state_strict_isolation(client):
    # 1. Persona switch to SNO Maharashtra keeps strict_isolation True
    sno_switch = client.post("/api/auth/switch-persona", json={"persona_id": "state_nodal_officer"})
    assert sno_switch.status_code == 200
    sno_data = sno_switch.json()
    assert sno_data["user"]["strict_isolation"] is True
    sno_token = sno_data["access_token"]

    # SNO Maharashtra querying works gets only Maharashtra works
    sno_works = client.get("/api/works", headers={"Authorization": f"Bearer {sno_token}"})
    assert sno_works.status_code == 200
    assert sno_works.json()["total"] > 0
    states = set(w["state_name"].upper() for w in sno_works.json()["items"])
    assert states == {"MAHARASHTRA"}

    # SNO Maharashtra cannot query Uttar Pradesh
    sno_up = client.get("/api/works?state=UTTAR%20PRADESH", headers={"Authorization": f"Bearer {sno_token}"})
    assert sno_up.status_code == 403
    assert "access denied" in sno_up.json()["detail"].lower()

    # 2. Persona switch to DM Pune keeps strict_isolation True
    dm_switch = client.post("/api/auth/switch-persona", json={"persona_id": "district_authority"})
    assert dm_switch.status_code == 200
    dm_data = dm_switch.json()
    assert dm_data["user"]["strict_isolation"] is True
    dm_token = dm_data["access_token"]

    # DM Pune cannot query UP works
    dm_up = client.get("/api/works?state=UTTAR%20PRADESH", headers={"Authorization": f"Bearer {dm_token}"})
    assert dm_up.status_code == 403

    # DM Pune cannot inspect MP from Varanasi, UP
    dm_mp_up = client.get("/api/mps/Narendra%20Modi", headers={"Authorization": f"Bearer {dm_token}"})
    assert dm_mp_up.status_code == 403
    assert "access denied" in dm_mp_up.json()["detail"].lower()

    # 3. MP Supriya Sule (Maharashtra) cannot query UP works
    mp_switch = client.post("/api/auth/switch-persona", json={"persona_id": "mp_user"})
    assert mp_switch.status_code == 200
    mp_token = mp_switch.json()["access_token"]

    mp_up = client.get("/api/works?state=UTTAR%20PRADESH", headers={"Authorization": f"Bearer {mp_token}"})
    assert mp_up.status_code == 403
    assert "access denied" in mp_up.json()["detail"].lower()

