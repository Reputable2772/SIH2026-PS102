"""
Investigation Center & Case Management Service (Pillars 7, 9, 17, 18).
Manages full Detect -> Explain -> Review -> Field Verify -> Resolve investigation lifecycle
with continuous feedback loop for AI risk engine calibration.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.config import BASE_DIR
from backend.services.data_service import DataService

DB_PATH = BASE_DIR / "backend" / "data" / "audit_store.db"

STAGES = [
    "FLAGGED",
    "UNDER_REVIEW",
    "FIELD_VERIFICATION",
    "ESCALATED",
    "RESOLVED_CLEARED",
    "CLOSED",
]


class InvestigationService:
    _instance: Optional["InvestigationService"] = None

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ds = DataService.get_instance()
        self._init_db()
        self._seed_initial_cases()

    @classmethod
    def get_instance(cls) -> "InvestigationService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables for investigation cases, timeline history, and model feedback."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS investigation_cases (
                    case_id TEXT PRIMARY KEY,
                    work_rec_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    stage TEXT NOT NULL DEFAULT 'FLAGGED',
                    risk_score REAL NOT NULL DEFAULT 50.0,
                    priority TEXT NOT NULL DEFAULT 'HIGH',
                    assigned_to TEXT NOT NULL DEFAULT 'Unassigned',
                    assigned_agency TEXT NOT NULL DEFAULT 'District Vigilance Cell',
                    state_name TEXT NOT NULL,
                    district_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    sanction_amount REAL NOT NULL DEFAULT 0.0,
                    evidence_notes TEXT NOT NULL DEFAULT '[]',
                    findings TEXT NOT NULL DEFAULT '',
                    calibration_feedback TEXT NOT NULL DEFAULT 'NONE',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS case_stage_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    from_stage TEXT,
                    to_stage TEXT NOT NULL,
                    changed_by TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _seed_initial_cases(self):
        """Seeds realistic high-risk works into investigation cases if table is empty."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) as cnt FROM investigation_cases")
            if cur.fetchone()["cnt"] > 0:
                return

            df = self.ds.df_works
            if df.empty:
                return

            # Grab top high-risk / critical priority projects across diverse states
            high_priority = df[df["priority"].isin(["CRITICAL", "HIGH"])].head(35)
            now_iso = datetime.now(timezone.utc).isoformat()

            cases_to_insert = []
            history_to_insert = []

            for idx, (_, row) in enumerate(high_priority.iterrows()):
                rec_id = str(row.get("WORK_RECOMMENDATION_DTL_ID"))
                case_id = f"CASE-{rec_id}"
                desc = str(row.get("WORK_DESCRIPTION", f"Infrastructure Audit #{rec_id}"))
                title = (desc[:75] + "...") if len(desc) > 75 else desc

                # Assign realistic stages across the pipeline
                stage = STAGES[idx % len(STAGES)]
                risk_info = self.ds.compute_explainable_risk(row)
                score = float(risk_info.get("score", 75.0))
                score = min(98.0, max(65.0, score))

                agencies = [
                    "District Vigilance Cell",
                    "DQM Flying Squad",
                    "MoSPI Internal Audit Division",
                    "State PWD Quality Wing",
                ]
                officers = [
                    "Er. Vikramaditya Sen (Senior DQM)",
                    "Sunita Rao (District Auditor)",
                    "Anand Kumar (Vigilance Inspector)",
                    "Dr. Rajesh Verma (MoSPI Oversight)",
                ]

                assigned_agency = agencies[idx % len(agencies)]
                assigned_to = officers[idx % len(officers)]
                priority = str(row.get("priority", "HIGH"))

                notes = [
                    {
                        "author": "Autonomous Risk Engine",
                        "text": f"Flagged by composite diagnostic score ({round(score)}/100). Significant cost or delay anomaly detected.",
                        "timestamp": now_iso,
                    }
                ]
                if stage in ["FIELD_VERIFICATION", "ESCALATED", "RESOLVED_CLEARED", "CLOSED"]:
                    notes.append(
                        {
                            "author": assigned_to,
                            "text": f"Physical site inspection dispatched via {assigned_agency}. Geotagged evidence pending review.",
                            "timestamp": now_iso,
                        }
                    )

                cases_to_insert.append(
                    (
                        case_id,
                        rec_id,
                        title,
                        stage,
                        score,
                        priority,
                        assigned_to,
                        assigned_agency,
                        str(row.get("STATE_NAME", "NATIONAL")),
                        str(row.get("IDA_NAME", "DISTRICT")),
                        str(row.get("WORK_CATEGORY", "Public Works")),
                        float(row.get("SANCTION_AMOUNT", 0.0)),
                        json.dumps(notes),
                        "Preliminary verification initiated under SIH26102 audit protocol.",
                        "NONE",
                        now_iso,
                        now_iso,
                    )
                )

                history_to_insert.append(
                    (
                        case_id,
                        None,
                        stage,
                        "System Audit Core",
                        "Initial case ingestion from anomaly pipeline",
                        now_iso,
                    )
                )

            conn.executemany(
                """
                INSERT INTO investigation_cases (
                    case_id, work_rec_id, title, stage, risk_score, priority,
                    assigned_to, assigned_agency, state_name, district_name, category,
                    sanction_amount, evidence_notes, findings, calibration_feedback,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                cases_to_insert,
            )
            conn.executemany(
                """
                INSERT INTO case_stage_history (
                    case_id, from_stage, to_stage, changed_by, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                history_to_insert,
            )
            conn.commit()
            print(f"[✓] InvestigationService seeded {len(cases_to_insert)} representative investigation cases.")

    def get_cases(
        self,
        scope: Optional[Dict[str, Any]] = None,
        stage: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves investigation cases with multi-tenant RBAC enforcement."""
        query = "SELECT * FROM investigation_cases WHERE 1=1"
        params: List[Any] = []

        if stage and stage in STAGES:
            query += " AND stage = ?"
            params.append(stage)

        if priority:
            query += " AND priority = ?"
            params.append(priority.upper())

        # Strict Multi-Tenant Isolation
        if scope and scope.get("strict_isolation", True):
            role = scope.get("role")
            if role == "DISTRICT_AUTHORITY":
                u_dist = str(scope.get("IDA_NAME", "")).strip().upper()
                query += " AND UPPER(district_name) LIKE ?"
                params.append(f"%{u_dist}%")
            elif role == "STATE_NODAL_OFFICER":
                u_state = str(scope.get("STATE_NAME", "")).strip().upper()
                query += " AND UPPER(state_name) = ?"
                params.append(u_state)
            elif role == "MP_USER":
                u_mp = str(scope.get("MP_NAME", "")).strip().lower()
                u_state = str(scope.get("STATE_NAME", "")).strip().upper()
                query += " AND (LOWER(title) LIKE ? OR UPPER(state_name) = ?)"
                params.extend([f"%{u_mp}%", u_state])

        query += " ORDER BY updated_at DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["evidence_notes"] = json.loads(item["evidence_notes"])
                if search:
                    sq = search.lower()
                    if (
                        sq not in item["title"].lower()
                        and sq not in item["work_rec_id"].lower()
                        and sq not in item["district_name"].lower()
                        and sq not in item["assigned_to"].lower()
                    ):
                        continue
                results.append(item)
            return results

    def update_stage(
        self,
        case_id: str,
        to_stage: str,
        changed_by: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Transitions case to another stage in the Kanban workflow."""
        if to_stage not in STAGES:
            raise ValueError(f"Invalid stage: {to_stage}. Must be one of {STAGES}")

        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT stage FROM investigation_cases WHERE case_id = ?",
                (case_id,),
            )
            row = cur.fetchone()
            if not row:
                raise KeyError(f"Case {case_id} not found")

            from_stage = row["stage"]
            conn.execute(
                """
                UPDATE investigation_cases
                SET stage = ?, updated_at = ?
                WHERE case_id = ?
                """,
                (to_stage, now_iso, case_id),
            )
            conn.execute(
                """
                INSERT INTO case_stage_history (case_id, from_stage, to_stage, changed_by, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (case_id, from_stage, to_stage, changed_by, notes, now_iso),
            )
            conn.commit()

        return self.get_case_detail(case_id)

    def add_evidence_note(
        self,
        case_id: str,
        note_text: str,
        author: str,
    ) -> Dict[str, Any]:
        """Appends an investigator evidence note or field finding."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT evidence_notes FROM investigation_cases WHERE case_id = ?",
                (case_id,),
            )
            row = cur.fetchone()
            if not row:
                raise KeyError(f"Case {case_id} not found")

            notes = json.loads(row["evidence_notes"])
            notes.append(
                {
                    "author": author,
                    "text": note_text,
                    "timestamp": now_iso,
                }
            )

            conn.execute(
                """
                UPDATE investigation_cases
                SET evidence_notes = ?, updated_at = ?
                WHERE case_id = ?
                """,
                (json.dumps(notes), now_iso, case_id),
            )
            conn.commit()

        return self.get_case_detail(case_id)

    def submit_calibration_feedback(
        self,
        case_id: str,
        feedback: str,  # CONFIRMED_ANOMALY, FALSE_POSITIVE, POLICY_EXEMPTION
        findings: str,
        author: str,
    ) -> Dict[str, Any]:
        """Records human-in-the-loop calibration feedback to refine AI detector weights."""
        valid_feedback = {"CONFIRMED_ANOMALY", "FALSE_POSITIVE", "POLICY_EXEMPTION"}
        if feedback not in valid_feedback:
            raise ValueError(f"Invalid feedback '{feedback}'. Must be one of {valid_feedback}")

        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE investigation_cases
                SET calibration_feedback = ?, findings = ?, updated_at = ?
                WHERE case_id = ?
                """,
                (feedback, findings, now_iso, case_id),
            )
            # Also log as an evidence note
            cur = conn.execute(
                "SELECT evidence_notes FROM investigation_cases WHERE case_id = ?",
                (case_id,),
            )
            row = cur.fetchone()
            notes = json.loads(row["evidence_notes"]) if row else []
            notes.append(
                {
                    "author": author,
                    "text": f"Calibration feedback submitted: {feedback}. Findings: {findings}",
                    "timestamp": now_iso,
                }
            )
            conn.execute(
                "UPDATE investigation_cases SET evidence_notes = ? WHERE case_id = ?",
                (json.dumps(notes), case_id),
            )
            conn.commit()

        return self.get_case_detail(case_id)

    def get_case_detail(self, case_id: str) -> Dict[str, Any]:
        """Returns full case detail including timeline history."""
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM investigation_cases WHERE case_id = ?",
                (case_id,),
            )
            row = cur.fetchone()
            if not row:
                raise KeyError(f"Case {case_id} not found")

            item = dict(row)
            item["evidence_notes"] = json.loads(item["evidence_notes"])

            hist_cur = conn.execute(
                "SELECT * FROM case_stage_history WHERE case_id = ? ORDER BY created_at ASC",
                (case_id,),
            )
            item["history"] = [dict(h) for h in hist_cur.fetchall()]
            return item

    def get_summary_stats(self, scope: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Returns investigation pipeline KPI aggregates."""
        cases = self.get_cases(scope=scope)

        stage_counts = {s: 0 for s in STAGES}
        priority_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        total_sanction_at_risk = 0.0

        for c in cases:
            st = c.get("stage", "FLAGGED")
            if st in stage_counts:
                stage_counts[st] += 1
            p = c.get("priority", "HIGH")
            if p in priority_counts:
                priority_counts[p] += 1
            if st not in ["RESOLVED_CLEARED", "CLOSED"]:
                total_sanction_at_risk += c.get("sanction_amount", 0.0)

        # Calibration stats
        calibrated_count = sum(1 for c in cases if c.get("calibration_feedback") != "NONE")
        confirmed_anomalies = sum(1 for c in cases if c.get("calibration_feedback") == "CONFIRMED_ANOMALY")
        false_positives = sum(1 for c in cases if c.get("calibration_feedback") == "FALSE_POSITIVE")
        policy_exemptions = sum(1 for c in cases if c.get("calibration_feedback") == "POLICY_EXEMPTION")
        total_eval = confirmed_anomalies + false_positives
        precision_pct = round((confirmed_anomalies / total_eval) * 100, 1) if total_eval > 0 else 100.0

        return {
            "total_active_cases": len(cases),
            "stages": stage_counts,
            "priorities": priority_counts,
            "total_funds_under_investigation": round(total_sanction_at_risk, 2),
            "model_calibration": {
                "total_calibrated": calibrated_count,
                "confirmed_anomalies": confirmed_anomalies,
                "false_positives": false_positives,
                "policy_exemptions": policy_exemptions,
                "precision_rate_pct": precision_pct,
            },
        }
