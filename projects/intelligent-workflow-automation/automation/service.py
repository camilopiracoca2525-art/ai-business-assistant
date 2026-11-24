import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import httpx

MOCK_CUSTOMERS = {
    "C-1001": {"name": "Northwind Demo", "email": "operations@example.com"},
    "C-1002": {"name": "Contoso Demo", "email": "purchasing@example.com"},
}

class WorkflowService:
    """Small SQLite-backed workflow runner for portfolio/demo use."""

    def __init__(
        self,
        database_path: str = "automation.db",
        webhook_url: str = "",
        max_attempts: int = 3,
        retry_delay_seconds: float = 0.2,
        delivery_adapter: Callable[[dict], None] | None = None,
    ):
        self.database_path = database_path
        self.webhook_url = webhook_url.strip()
        self.max_attempts = max(1, max_attempts)
        self.retry_delay_seconds = max(0.0, retry_delay_seconds)
        self.delivery_adapter = delivery_adapter
        Path(database_path).parent.mkdir(parents=True, exist_ok=True) if Path(database_path).parent != Path(".") else None
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    run_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    result_json TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS workflow_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    step TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES workflow_runs(run_id)
                )
            """)

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _event(self, run_id: str, step: str, status: str, details: dict):
        with self._connect() as db:
            db.execute(
                "INSERT INTO workflow_events(run_id, step, status, details, created_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, step, status, json.dumps(details), self._now()),
            )

    def _set_run(self, run_id: str, status: str, result: dict, attempts: int):
        with self._connect() as db:
            db.execute(
                "UPDATE workflow_runs SET status=?, result_json=?, attempts=?, updated_at=? WHERE run_id=?",
                (status, json.dumps(result), attempts, self._now(), run_id),
            )

    def _deliver(self, payload: dict):
        if self.delivery_adapter is not None:
            self.delivery_adapter(payload)
        elif self.webhook_url:
            response = httpx.post(self.webhook_url, json=payload, timeout=10.0)
            response.raise_for_status()
        # Without an adapter or URL, delivery is simulated for local demo mode.

    def get_run(self, run_id: str):
        with self._connect() as db:
            row = db.execute("SELECT * FROM workflow_runs WHERE run_id=?", (run_id,)).fetchone()
            if row is None:
                return None
            events = db.execute(
                "SELECT step, status, details, created_at FROM workflow_events WHERE run_id=? ORDER BY event_id",
                (run_id,),
            ).fetchall()
        return {
            "run_id": row["run_id"],
            "idempotency_key": row["idempotency_key"],
            "status": row["status"],
            "attempts": row["attempts"],
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
            "events": [
                {"step": e["step"], "status": e["status"], "details": json.loads(e["details"]), "created_at": e["created_at"]}
                for e in events
            ],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def run(self, customer_id: str, request_text: str, idempotency_key: str | None = None):
        key = (idempotency_key or str(uuid.uuid4())).strip()
        if not key:
            raise ValueError("idempotency_key cannot be blank")
        if not customer_id.strip() or not request_text.strip():
            raise ValueError("customer_id and request_text are required")

        with self._connect() as db:
            existing = db.execute(
                "SELECT run_id FROM workflow_runs WHERE idempotency_key=?", (key,)
            ).fetchone()
            if existing:
                return self.get_run(existing["run_id"])

            run_id = str(uuid.uuid4())
            now = self._now()
            db.execute(
                "INSERT INTO workflow_runs(run_id, idempotency_key, status, input_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, key, "running", json.dumps({"customer_id": customer_id, "request_text": request_text}), now, now),
            )

        attempts = 0
        try:
            self._event(run_id, "validate_request", "completed", {"valid": True})
            customer = MOCK_CUSTOMERS.get(customer_id)
            if customer is None:
                raise ValueError(f"Customer '{customer_id}' was not found in the mock CRM.")

            self._event(run_id, "lookup_customer", "completed", {"customer_id": customer_id})
            notification = {
                "event": "business_workflow.completed",
                "run_id": run_id,
                "customer": customer,
                "message": request_text,
                "source": "intelligent-workflow-automation",
            }
            self._event(run_id, "prepare_notification", "completed", {"customer_name": customer["name"]})

            last_error = None
            for attempt in range(1, self.max_attempts + 1):
                attempts = attempt
                try:
                    self._deliver(notification)
                    self._event(run_id, "deliver_notification", "completed", {"attempt": attempt, "mode": "webhook" if (self.webhook_url or self.delivery_adapter) else "simulated"})
                    result = {"message": "Workflow completed successfully.", "customer": customer["name"], "delivery": "sent" if (self.webhook_url or self.delivery_adapter) else "simulated"}
                    self._set_run(run_id, "completed", result, attempts)
                    return self.get_run(run_id)
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    self._event(run_id, "deliver_notification", "retrying" if attempt < self.max_attempts else "failed", {"attempt": attempt, "error": last_error})
                    if attempt < self.max_attempts and self.retry_delay_seconds:
                        time.sleep(self.retry_delay_seconds * (2 ** (attempt - 1)))

            raise RuntimeError(f"Delivery failed after {attempts} attempts: {last_error}")
        except Exception as exc:
            result = {"message": "Workflow failed.", "error": f"{type(exc).__name__}: {exc}"}
            self._set_run(run_id, "failed", result, attempts)
            self._event(run_id, "workflow", "failed", result)
            return self.get_run(run_id)

    def recent_runs(self, limit: int = 20):
        with self._connect() as db:
            rows = db.execute(
                "SELECT run_id FROM workflow_runs ORDER BY created_at DESC LIMIT ?",
                (max(1, min(limit, 100)),),
            ).fetchall()
        return [self.get_run(row["run_id"]) for row in rows]
