"""
MPLADS Intelligence Engine — Self-Contained Interactive HTML Report Generator.

Generates standalone, responsive, interactive HTML audit reports and case dossiers
with zero external runtime dependencies. Suitable for offline inspection by
auditors, district authorities, MoSPI oversight committees, and browser verification.
"""

import html
import json
from datetime import datetime
from typing import Any


def _sanitize(val: Any) -> str:
    """Escapes HTML entities for safe embedding."""
    if val is None:
        return "N/A"
    return html.escape(str(val))


def generate_dossier_html(dossier: Any) -> str:
    """
    Generates a standalone, beautiful HTML audit dossier for a single work.
    """
    evidence_json = json.dumps(dossier.q4_supporting_evidence, indent=2, default=str)

    # Priority badge color
    prio = getattr(dossier, "priority", "NORMAL")
    prio_color_map = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MEDIUM": "#eab308",
        "LOW": "#3b82f6",
        "NORMAL": "#10b981",
    }
    prio_color = prio_color_map.get(str(prio).upper(), "#64748b")

    actions_html = "".join(
        f"""
        <li class="action-item">
            <input type="checkbox" id="act-{i}" class="action-check">
            <label for="act-{i}">{_sanitize(act)}</label>
        </li>
        """
        for i, act in enumerate(dossier.next_review_actions, 1)
    )

    raw_findings = getattr(dossier, "constituent_findings", getattr(dossier, "findings", []))
    findings_badges = "".join(
        f'<span class="badge badge-anomaly">{_sanitize(f.get("detector_code") if isinstance(f, dict) else getattr(f, "detector_code", ""))}</span>'
        for f in raw_findings
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audit Dossier — Work Rec #{_sanitize(dossier.work_rec_id)}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-card: #182234;
            --border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --prio-color: {prio_color};
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background: var(--bg); color: var(--text-main); line-height: 1.6; padding: 2rem; }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        .header {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
        .header-top {{ display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; }}
        .title-badge {{ display: flex; align-items: center; gap: 0.75rem; }}
        .badge {{ padding: 0.35rem 0.75rem; border-radius: 9999px; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; }}
        .badge-prio {{ background: var(--prio-color); color: #fff; }}
        .badge-anomaly {{ background: #334155; color: #38bdf8; margin-right: 0.4rem; font-size: 0.8rem; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-top: 1.5rem; }}
        .kpi-card {{ background: var(--surface-card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; text-align: center; }}
        .kpi-val {{ font-size: 1.4rem; font-weight: 800; color: var(--accent); }}
        .kpi-lbl {{ font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }}
        .section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.75rem; margin-bottom: 1.5rem; }}
        .section-title {{ font-size: 1.15rem; font-weight: 700; color: var(--accent); margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }}
        .q-box {{ background: var(--surface-card); border-left: 4px solid var(--accent); padding: 1rem; border-radius: 0 8px 8px 0; margin-bottom: 1rem; }}
        pre {{ background: #0b1120; border: 1px solid var(--border); border-radius: 8px; padding: 1rem; overflow-x: auto; color: #a5f3fc; font-size: 0.85rem; }}
        .action-list {{ list-style: none; }}
        .action-item {{ display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.75rem; border-bottom: 1px solid var(--border); }}
        .action-item:last-child {{ border-bottom: none; }}
        .action-check {{ margin-top: 0.35rem; width: 1.1rem; height: 1.1rem; accent-color: var(--accent); cursor: pointer; }}
        .action-item label {{ cursor: pointer; }}
        .print-btn {{ background: var(--accent); color: #0f172a; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; font-weight: 700; cursor: pointer; transition: opacity 0.2s; }}
        .print-btn:hover {{ opacity: 0.9; }}
        @media print {{
            body {{ background: #fff; color: #000; padding: 0; }}
            .section, .header {{ border: 1px solid #ccc; background: #fff; color: #000; box-shadow: none; }}
            .kpi-card, .q-box {{ background: #f8fafc; border: 1px solid #e2e8f0; }}
            .print-btn {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-top">
                <div>
                    <div class="title-badge">
                        <h1>MPLADS Audit Dossier</h1>
                        <span class="badge badge-prio">{_sanitize(dossier.priority)}</span>
                    </div>
                    <p style="color: var(--text-muted); margin-top: 0.4rem;">
                        Work Recommendation ID: <strong>#{_sanitize(dossier.work_rec_id)}</strong> | Physical Work ID: <strong>{_sanitize(dossier.work_id)}</strong>
                    </p>
                </div>
                <button class="print-btn" onclick="window.print()">Print / Export PDF</button>
            </div>

            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-val">{dossier.composite_severity:.2f}</div>
                    <div class="kpi-lbl">Composite Severity</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-val">{dossier.composite_confidence:.2f}</div>
                    <div class="kpi-lbl">Confidence Score</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-val">₹{dossier.sanction_amount:,.0f}</div>
                    <div class="kpi-lbl">Sanction Amount</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-val">{_sanitize(dossier.state_name)}</div>
                    <div class="kpi-lbl">State / District: {_sanitize(dossier.ida_name)}</div>
                </div>
            </div>

            <div style="margin-top: 1.25rem;">
                <span style="color: var(--text-muted); font-size: 0.85rem; margin-right: 0.5rem;">Triggered Detectors:</span>
                {findings_badges if findings_badges else '<span style="color: var(--text-muted);">None (Clean)</span>'}
            </div>
        </div>

        <!-- 5 Governance Questions -->
        <div class="section">
            <h2 class="section-title">Q1: What Happened?</h2>
            <div class="q-box">
                <p>{_sanitize(dossier.q1_what_happened)}</p>
            </div>

            <h2 class="section-title">Q2: Why Is It Unusual?</h2>
            <div class="q-box">
                <p>{_sanitize(dossier.q2_why_unusual)}</p>
            </div>

            <h2 class="section-title">Q3: Compared With What?</h2>
            <div class="q-box">
                <p>{_sanitize(dossier.q3_compared_with_what)}</p>
            </div>

            <h2 class="section-title">Q4: Supporting Evidence & Telemetry</h2>
            <pre><code>{evidence_json}</code></pre>

            <h2 class="section-title" style="margin-top: 1.5rem;">Q5: Known Data Limitations</h2>
            <div class="q-box" style="border-left-color: #f59e0b;">
                <p>{_sanitize(dossier.q5_limitations)}</p>
            </div>
        </div>

        <!-- Recommended Review Actions (AC-19) -->
        <div class="section">
            <h2 class="section-title" style="color: #4ade80;">Recommended Next Review Actions (Statutory AC-19 Checklist)</h2>
            <ul class="action-list">
                {actions_html if actions_html else '<li class="action-item"><label>No immediate action required.</label></li>'}
            </ul>
        </div>
    </div>
</body>
</html>
"""


def generate_audit_report_html(results: Any, title: str = "MPLADS Intelligence Engine — Audit Findings Report") -> str:
    """
    Generates a full, self-contained interactive HTML audit report containing
    KPI summaries, SVG charts, and a filterable/searchable table of prioritized cases.
    """
    scores = getattr(results, "scores", [])
    findings = getattr(results, "findings", [])
    total_works = len(scores)

    # Priority counts
    prio_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NORMAL": 0}
    for s in scores:
        p = str(s.priority.value if hasattr(s.priority, "value") else s.priority).upper()
        prio_counts[p] = prio_counts.get(p, 0) + 1

    critical_count = prio_counts.get("CRITICAL", 0)
    high_count = prio_counts.get("HIGH", 0)
    medium_count = prio_counts.get("MEDIUM", 0)

    # Build Case Rows
    rows_html = []
    for idx, s in enumerate(scores):
        prio_str = str(s.priority.value if hasattr(s.priority, "value") else s.priority).upper()
        prio_color = {
            "CRITICAL": "#ef4444",
            "HIGH": "#f97316",
            "MEDIUM": "#eab308",
            "LOW": "#3b82f6",
            "NORMAL": "#10b981",
        }.get(prio_str, "#64748b")

        finding_codes = [f.detector_code for f in getattr(s, "findings", [])]
        codes_str = ", ".join(finding_codes) if finding_codes else "None"
        work_rec_id = _sanitize(s.work_rec_id)
        state_name = _sanitize(s.state_name)
        ida_name = _sanitize(s.ida_name)
        sanction = f"₹{s.sanction_amount:,.0f}" if s.sanction_amount else "N/A"
        sev = f"{s.composite_severity:.2f}"
        conf = f"{s.composite_confidence:.2f}"

        first_action = s.findings[0].next_review_action if s.findings else "No immediate action required"

        row = f"""
        <tr class="work-row" data-priority="{prio_str}" data-state="{state_name}" data-search="{work_rec_id} {state_name} {ida_name} {codes_str}">
            <td><strong style="color: #38bdf8;">#{work_rec_id}</strong></td>
            <td>{state_name}<br><small style="color: #94a3b8;">{ida_name}</small></td>
            <td><span class="badge" style="background: {prio_color}; color: #fff;">{prio_str}</span></td>
            <td><strong>{sev}</strong></td>
            <td>{conf}</td>
            <td>{sanction}</td>
            <td><span class="anomaly-tag">{codes_str}</span></td>
            <td style="font-size: 0.85rem; color: #cbd5e1;">{_sanitize(first_action)}</td>
        </tr>
        """
        rows_html.append(row)

    rows_str = "\n".join(rows_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_sanitize(title)}</title>
    <style>
        :root {{
            --bg: #0b0f19;
            --surface: #151d2f;
            --surface-alt: #1c263d;
            --border: #2b3954;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.15);
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        body {{ background: var(--bg); color: var(--text-main); line-height: 1.5; padding: 2rem 1.5rem; }}
        .header {{ max-width: 1280px; margin: 0 auto 2rem; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 1rem; }}
        h1 {{ font-size: 1.85rem; font-weight: 800; color: #fff; letter-spacing: -0.02em; }}
        .subtitle {{ color: var(--text-muted); font-size: 0.95rem; margin-top: 0.25rem; }}

        .kpi-container {{ max-width: 1280px; margin: 0 auto 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
        .kpi-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem 1.5rem; }}
        .kpi-val {{ font-size: 1.9rem; font-weight: 800; color: #fff; margin-bottom: 0.25rem; }}
        .kpi-title {{ font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }}

        .table-section {{ max-width: 1280px; margin: 0 auto; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.4); }}

        .controls-bar {{ padding: 1.25rem 1.5rem; background: var(--surface-alt); border-bottom: 1px solid var(--border); display: flex; flex-wrap: wrap; gap: 1rem; justify-content: space-between; align-items: center; }}
        .search-box {{ flex: 1; min-width: 250px; position: relative; }}
        .search-input {{ width: 100%; background: #0b0f19; border: 1px solid var(--border); border-radius: 8px; padding: 0.6rem 1rem; color: #fff; font-size: 0.9rem; outline: none; }}
        .search-input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }}

        .filter-buttons {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}
        .btn-filter {{ background: #0b0f19; border: 1px solid var(--border); color: var(--text-muted); padding: 0.45rem 0.9rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all 0.15s ease; }}
        .btn-filter.active, .btn-filter:hover {{ background: var(--accent); color: #0b0f19; border-color: var(--accent); }}

        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }}
        th {{ background: #131a2a; color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; padding: 0.9rem 1.2rem; border-bottom: 1px solid var(--border); }}
        td {{ padding: 0.9rem 1.2rem; border-bottom: 1px solid #1f293d; }}
        tr:hover td {{ background: rgba(56, 189, 248, 0.04); }}

        .badge {{ padding: 0.25rem 0.65rem; border-radius: 9999px; font-weight: 700; font-size: 0.75rem; letter-spacing: 0.03em; }}
        .anomaly-tag {{ display: inline-block; background: #0f172a; border: 1px solid var(--border); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; color: #38bdf8; font-family: monospace; }}

        .table-footer {{ padding: 1rem 1.5rem; background: var(--surface-alt); font-size: 0.85rem; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center; }}
    </style>
</head>
<body>
    <header class="header">
        <div>
            <h1>{_sanitize(title)}</h1>
            <div class="subtitle">Autonomous Anomaly Detection, Risk Prioritization & Explainable Audit Findings (SIH PS102)</div>
        </div>
        <div style="font-size: 0.85rem; color: var(--text-muted); text-align: right;">
            Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
            Total Works Evaluated: <strong>{total_works:,}</strong>
        </div>
    </header>

    <section class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-val" style="color: #ef4444;">{critical_count:,}</div>
            <div class="kpi-title">Critical Attention</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #f97316;">{high_count:,}</div>
            <div class="kpi-title">High Priority</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #eab308;">{medium_count:,}</div>
            <div class="kpi-title">Medium Priority</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: var(--accent);">{len(findings):,}</div>
            <div class="kpi-title">Triggered Anomalies</div>
        </div>
    </section>

    <section class="table-section">
        <div class="controls-bar">
            <div class="search-box">
                <input type="text" id="searchInput" class="search-input" placeholder="Search by Work ID, State, District, Anomaly Code...">
            </div>
            <div class="filter-buttons">
                <button class="btn-filter active" onclick="filterPriority('ALL')">ALL</button>
                <button class="btn-filter" onclick="filterPriority('CRITICAL')">CRITICAL</button>
                <button class="btn-filter" onclick="filterPriority('HIGH')">HIGH</button>
                <button class="btn-filter" onclick="filterPriority('MEDIUM')">MEDIUM</button>
                <button class="btn-filter" onclick="filterPriority('LOW')">LOW</button>
            </div>
        </div>

        <div style="overflow-x: auto;">
            <table id="worksTable">
                <thead>
                    <tr>
                        <th>Work Rec ID</th>
                        <th>State / District</th>
                        <th>Priority</th>
                        <th>Severity</th>
                        <th>Confidence</th>
                        <th>Sanction</th>
                        <th>Anomalies</th>
                        <th>Next Review Action (AC-19)</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_str}
                </tbody>
            </table>
        </div>

        <div class="table-footer">
            <span id="rowsCount">Showing all {total_works:,} cases</span>
            <div class="pagination-controls" style="display: flex; gap: 0.5rem; align-items: center;">
                <button id="btnPrev" class="btn-filter" onclick="changePage(-1)">&larr; Prev</button>
                <span id="pageInfo" style="font-weight: 600; color: #fff;">Page 1 of 1</span>
                <button id="btnNext" class="btn-filter" onclick="changePage(1)">Next &rarr;</button>
            </div>
            <span>MPLADS Core Intelligence Engine &bull; Zero CDN &bull; Pure Offline Standard</span>
        </div>
    </section>

    <script>
        let currentPriority = 'ALL';
        let currentPage = 1;
        const pageSize = 50;
        const searchInput = document.getElementById('searchInput');
        const rows = Array.from(document.querySelectorAll('.work-row'));
        const countSpan = document.getElementById('rowsCount');
        const pageInfo = document.getElementById('pageInfo');
        const btnPrev = document.getElementById('btnPrev');
        const btnNext = document.getElementById('btnNext');

        let filteredRows = [...rows];

        function renderPage() {{
            const totalMatches = filteredRows.length;
            const totalPages = Math.max(1, Math.ceil(totalMatches / pageSize));
            if (currentPage > totalPages) currentPage = totalPages;
            if (currentPage < 1) currentPage = 1;

            const startIdx = (currentPage - 1) * pageSize;
            const endIdx = startIdx + pageSize;

            rows.forEach(r => r.style.display = 'none');
            for (let i = startIdx; i < endIdx && i < totalMatches; i++) {{
                filteredRows[i].style.display = '';
            }}

            countSpan.textContent = `Showing ${{Math.min(totalMatches, startIdx + 1)}}-${{Math.min(totalMatches, endIdx)}} of ${{totalMatches}} matching cases (${{rows.length}} total)`;
            pageInfo.textContent = `Page ${{currentPage}} of ${{totalPages}}`;
            btnPrev.disabled = (currentPage <= 1);
            btnNext.disabled = (currentPage >= totalPages);
            btnPrev.style.opacity = (currentPage <= 1) ? '0.5' : '1';
            btnNext.style.opacity = (currentPage >= totalPages) ? '0.5' : '1';
        }}

        function updateFilter() {{
            const query = searchInput.value.toLowerCase().trim();
            currentPage = 1;

            filteredRows = rows.filter(r => {{
                const p = r.getAttribute('data-priority');
                const s = r.getAttribute('data-search').toLowerCase();
                const matchesPrio = (currentPriority === 'ALL' || p === currentPriority);
                const matchesSearch = (!query || s.includes(query));
                return matchesPrio && matchesSearch;
            }});

            renderPage();
        }}

        function changePage(delta) {{
            currentPage += delta;
            renderPage();
        }}

        function filterPriority(prio) {{
            currentPriority = prio;
            document.querySelectorAll('.btn-filter').forEach(b => {{
                if (['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(b.textContent.trim())) {{
                    b.classList.toggle('active', b.textContent.trim() === prio);
                }}
            }});
            updateFilter();
        }}

        searchInput.addEventListener('input', updateFilter);
        updateFilter();
    </script>
</body>
</html>
"""
