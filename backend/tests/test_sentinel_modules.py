"""
Unit tests for the SIH26102 Sentinel & Nirikshak AI feature suite:
- Duplicate & Ghost Work Detection
- Investigation Center & Case Management (Kanban Lifecycle)
- Statutory Compliance Radar (15% SC, 7.5% ST, SLA, Prohibited Works)
- AI Priority Recommendations & MP Form 2B Draft Letter Generator
- Natural-Language Analytics Assistant
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_duplicates_endpoint_and_resolve():
    # 1. Fetch duplicates
    res = client.get("/api/duplicates?min_similarity=60.0&limit=10")
    assert res.status_code == 200
    pairs = res.json()
    assert isinstance(pairs, list)
    assert len(pairs) > 0

    first_pair = pairs[0]
    pair_id = first_pair["pair_id"]
    assert "similarity_pct" in first_pair
    assert "project_a" in first_pair
    assert "project_b" in first_pair
    assert first_pair["similarity_pct"] >= 60.0

    # 2. Get stats
    stats_res = client.get("/api/duplicates/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_pairs_flagged" in stats
    assert stats["total_pairs_flagged"] > 0

    # 3. Resolve pair
    headers = {"X-User-Role": "CENTRAL_AUDITOR"}
    resolve_res = client.post(
        f"/api/duplicates/{pair_id}/resolve",
        json={"decision": "CONFIRMED_DUPLICATE", "notes": "Audited via DQM site verification. Matched coordinates."},
        headers=headers,
    )
    assert resolve_res.status_code == 200
    res_data = resolve_res.json()
    assert res_data["status"] == "CONFIRMED_DUPLICATE"
    assert res_data["pair_id"] == pair_id


def test_investigations_lifecycle_and_calibration():
    # 1. Summary stats
    sum_res = client.get("/api/investigations/summary")
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert "stages" in summary
    assert "total_active_cases" in summary
    assert summary["total_active_cases"] > 0

    # 2. List cases
    list_res = client.get("/api/investigations")
    assert list_res.status_code == 200
    cases = list_res.json()
    assert len(cases) > 0

    case_id = cases[0]["case_id"]

    # 3. Update stage (Kanban transition)
    headers = {"X-User-Role": "DISTRICT_AUTHORITY", "X-IDA-Name": cases[0]["district_name"]}
    transition_res = client.patch(
        f"/api/investigations/{case_id}/stage",
        json={"to_stage": "FIELD_VERIFICATION", "notes": "Dispatched executive engineer for ground audit"},
        headers=headers,
    )
    assert transition_res.status_code == 200
    assert transition_res.json()["stage"] == "FIELD_VERIFICATION"

    # 4. Add evidence note
    note_res = client.post(
        f"/api/investigations/{case_id}/notes",
        json={"note": "Geotagged site photograph shows incomplete foundation."},
        headers=headers,
    )
    assert note_res.status_code == 200
    assert len(note_res.json()["evidence_notes"]) >= 2

    # 5. Model calibration feedback loop
    calib_headers = {"X-User-Role": "CENTRAL_AUDITOR"}
    calib_res = client.post(
        f"/api/investigations/{case_id}/calibrate",
        json={
            "feedback": "CONFIRMED_ANOMALY",
            "findings": "Physical completion was falsified as 85% whereas actual was 30%.",
        },
        headers=calib_headers,
    )
    assert calib_res.status_code == 200
    assert calib_res.json()["calibration_feedback"] == "CONFIRMED_ANOMALY"


def test_compliance_radar():
    res = client.get("/api/compliance")
    assert res.status_code == 200
    data = res.json()
    assert "overall_compliance_score" in data
    assert "sc_allocation" in data
    assert "st_allocation" in data
    assert "sla_performance" in data
    assert "prohibited_items" in data
    assert "statutory_checklist" in data

    assert data["sc_allocation"]["target_pct"] == 15.0
    assert data["st_allocation"]["target_pct"] == 7.5
    assert len(data["statutory_checklist"]) >= 4


def test_recommendations_and_draft_letter():
    # 1. Fetch AI recommendations
    recs_res = client.get("/api/recommendations")
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert len(recs) > 0
    assert "urgency_score" in recs[0]
    assert "category" in recs[0]

    # 2. Generate Draft Recommendation Letter (Authorized as MP User)
    mp_headers = {"X-Persona-Id": "mp_user"}
    letter_res = client.post(
        "/api/recommendations/draft-letter",
        json={
            "selected_rec_ids": [recs[0]["recommendation_id"]],
            "mp_name": "Smt. Supriya Sule",
            "constituency": "Baramati (Maharashtra)",
            "district_authority_name": "Pune District Collectorate",
        },
        headers=mp_headers,
    )
    assert letter_res.status_code == 200
    letter = letter_res.json()
    assert "ref_no" in letter
    assert "full_text" in letter
    assert "MPLADS Guidelines 2023" in letter["full_text"]
    assert "Baramati" in letter["full_text"]
    assert len(letter["itemized_works"]) >= 1


def test_natural_language_analytics():
    # 1. Query suggestions
    sug_res = client.get("/api/analytics/suggestions")
    assert sug_res.status_code == 200
    assert len(sug_res.json()) > 0

    # 2. Run query
    query_payload = {"query": "Show delayed road works in Maharashtra"}
    q_res = client.post("/api/analytics/query", json=query_payload)
    assert q_res.status_code == 200
    ans = q_res.json()
    assert "summary" in ans
    assert "metrics" in ans
    assert "results" in ans
    assert isinstance(ans["results"], list)
