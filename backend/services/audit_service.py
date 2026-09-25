"""
SQLite Persistence Service for AC-19 Review Actions & Audit Trail.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.core.config import BASE_DIR

DB_PATH = Path(os.environ.get("AUDIT_DB_PATH", str(BASE_DIR / "backend" / "data" / "audit_store.db")))


class AuditService:
    """Manages persistent audit trail and AC-19 checklist sign-offs."""

    _instance = None

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @classmethod
    def get_instance(cls) -> "AuditService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables for review actions and audit logs."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS work_review_actions (
                    work_rec_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'UNDER_REVIEW',
                    checked_actions TEXT NOT NULL DEFAULT '[]',
                    auditor_notes TEXT NOT NULL DEFAULT '',
                    auditor_name TEXT NOT NULL DEFAULT 'Oversight Officer',
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_rec_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    actor_name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get_review_state(self, work_rec_id: str) -> Dict[str, Any]:
        """Retrieves saved review actions and status for a work."""
        rec_id = str(work_rec_id).strip()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM work_review_actions WHERE work_rec_id = ?",
                (rec_id,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "work_rec_id": row["work_rec_id"],
                    "status": row["status"],
                    "checked_actions": json.loads(row["checked_actions"]),
                    "auditor_notes": row["auditor_notes"],
                    "auditor_name": row["auditor_name"],
                    "updated_at": row["updated_at"],
                }
            return {
                "work_rec_id": rec_id,
                "status": "UNDER_REVIEW",
                "checked_actions": [],
                "auditor_notes": "",
                "auditor_name": "Dr. Rajesh Verma (MoSPI Oversight)",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

    def save_review_state(
        self,
        work_rec_id: str,
        status: str,
        checked_actions: List[str],
        auditor_notes: str = "",
        auditor_name: str = "Oversight Officer",
    ) -> Dict[str, Any]:
        """Saves or updates review actions and logs the audit event."""
        rec_id = str(work_rec_id).strip()
        now_iso = datetime.now(timezone.utc).isoformat()
        actions_json = json.dumps(checked_actions)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO work_review_actions (work_rec_id, status, checked_actions, auditor_notes, auditor_name, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(work_rec_id) DO UPDATE SET
                    status=excluded.status,
                    checked_actions=excluded.checked_actions,
                    auditor_notes=excluded.auditor_notes,
                    auditor_name=excluded.auditor_name,
                    updated_at=excluded.updated_at
                """,
                (rec_id, status, actions_json, auditor_notes, auditor_name, now_iso),
            )
            conn.execute(
                """
                INSERT INTO audit_activity_log (work_rec_id, action_type, details, actor_name, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    rec_id,
                    "REVIEW_UPDATED",
                    f"Status set to {status} with {len(checked_actions)} actions completed",
                    auditor_name,
                    now_iso,
                ),
            )
            conn.commit()

        return self.get_review_state(rec_id)
