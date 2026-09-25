"""
5-Question Governance Dossier & AC-19 Checklist Endpoints.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from backend.core.auth import get_tenant_scope
from backend.services.data_service import DataService

router = APIRouter(prefix="/dossier", tags=["Audit Dossier & Governance"])


@router.get("/{rec_id}", response_model=Dict[str, Any])
def get_governance_dossier(
    rec_id: str,
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Generates the 5-question explainable audit dossier with AC-19 Action Checklist and RBAC scoping."""
    ds = DataService.get_instance()
    try:
        return ds.get_work_dossier(rec_id, scope=scope)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{rec_id}/html", response_class=HTMLResponse)
def export_dossier_html(
    rec_id: str,
    scope: Dict[str, Any] = Depends(get_tenant_scope),
):
    """Renders standalone, self-contained interactive HTML dossier for download or print."""
    ds = DataService.get_instance()
    try:
        d = ds.get_work_dossier(rec_id, scope=scope)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    signals_html = "".join(
        f"<div style='margin-bottom:8px;padding:8px;background:#0f172a;border-radius:6px;border-left:3px solid #f97316;'>"
        f"<strong>+{s['weight']} {s['name']}</strong> ({s['severity']})<br/>"
        f"<span style='color:#94a3b8;font-size:0.9em;'>{s['explanation']}</span><br/>"
        f"<span style='color:#38bdf8;font-size:0.85em;'>→ Recommended: {s['action']}</span></div>"
        for s in d.get("risk_signals", [])
    )

    evidence_dict = d["five_questions"].get("q4_supporting_evidence", {})
    evidence_items = (
        "".join(f"<li><strong>{k.replace('_', ' ').title()}:</strong> {v}</li>" for k, v in evidence_dict.items())
        if isinstance(evidence_dict, dict)
        else f"<p>{evidence_dict}</p>"
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>MPLADS Audit Dossier — Work {rec_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; background: #0f172a; color: #f8fafc; line-height: 1.6; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 1px solid #334155; }}
        h1 {{ color: #38bdf8; margin-top: 0; }}
        h2 {{ color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 8px; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-weight: bold; background: #ef4444; color: white; }}
        .score-pill {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-weight: bold; background: #0284c7; color: white; margin-left: 8px; }}
        .qa {{ margin-bottom: 16px; }}
        .q {{ font-weight: 600; color: #cbd5e1; margin-bottom: 4px; }}
        .a {{ color: #94a3b8; background: #0f172a; padding: 12px; border-radius: 6px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; color: #e2e8f0; }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">{d["priority"]} PRIORITY</span>
        <span class="score-pill">RISK SCORE: {d.get("risk_score", 50)} / 100</span>
        <h1>Governance Dossier: Work #{d["work_rec_id"]}</h1>
        <p><strong>Description:</strong> {d["description"]}</p>
        <p><strong>Location:</strong> {d["ida_name"]}, {d["state_name"]} | <strong>MP:</strong> {d["mp_name"]}</p>
        <p><strong>Sanctioned:</strong> ₹{d["sanction_amount"]:,.0f} | <strong>Disbursed:</strong> ₹{d["total_disbursed"]:,.0f}</p>
    </div>

    <div class="card">
        <h2>Explainable Risk Diagnostics &amp; Contributing Signals</h2>
        {signals_html if signals_html else "<p style='color:#94a3b8;'>Baseline statistical parameters. No guideline breaches detected.</p>"}
    </div>

    <div class="card">
        <h2>5 Core Governance Questions</h2>
        <div class="qa"><div class="q">Q1: What happened?</div><div class="a">{d["five_questions"]["q1_what_happened"]}</div></div>
        <div class="qa"><div class="q">Q2: Why is it unusual?</div><div class="a">{d["five_questions"]["q2_why_unusual"]}</div></div>
        <div class="qa"><div class="q">Q3: Compared with what?</div><div class="a">{d["five_questions"]["q3_compared_with_what"]}</div></div>
        <div class="qa"><div class="q">Q4: What empirical evidence supports the anomalous categorization?</div><div class="a"><ul>{evidence_items}</ul></div></div>
        <div class="qa"><div class="q">Q5: What are the analytical boundaries and limitations?</div><div class="a">{d["five_questions"]["q5_limitations"]}</div></div>
    </div>

    <div class="card">
        <h2>Prescribed AC-19 Action Checklist for Reviewing Authority</h2>
        <ul>
            {"".join(f"<li>☑ {action}</li>" for action in d["next_review_actions"])}
        </ul>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html)
