"""SQLite persistence adapter for events, states and snapshots."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..core.events import TwinEvent


class SQLiteStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS event_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    plant_id TEXT,
                    entity_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS state_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    plant_id TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    state TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_event_logs_entity ON event_logs(entity_id);
                CREATE INDEX IF NOT EXISTS idx_event_logs_type ON event_logs(type);
                CREATE INDEX IF NOT EXISTS idx_event_logs_ts ON event_logs(ts);

                CREATE INDEX IF NOT EXISTS idx_state_history_entity ON state_history(entity_id);
                CREATE INDEX IF NOT EXISTS idx_state_history_plant ON state_history(plant_id);
                CREATE INDEX IF NOT EXISTS idx_state_history_ts ON state_history(ts);
                """
            )
            conn.commit()

    def persist_event(self, event: TwinEvent) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO event_logs (ts, plant_id, entity_id, type, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.timestamp.isoformat(),
                    event.plant_id,
                    event.entity_id,
                    event.type,
                    json.dumps(event.payload, ensure_ascii=True, separators=(",", ":")),
                ),
            )
            conn.commit()

    def persist_state(
        self,
        *,
        plant_id: str,
        entity_id: str,
        state: dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> None:
        ts = timestamp or datetime.now(timezone.utc)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO state_history (ts, plant_id, entity_id, state)
                VALUES (?, ?, ?, ?)
                """,
                (ts.isoformat(), plant_id, entity_id, json.dumps(state, ensure_ascii=True, separators=(",", ":"))),
            )
            conn.commit()

    def persist_snapshot(self, *, payload: dict[str, Any], timestamp: Optional[datetime] = None) -> None:
        ts = timestamp or datetime.now(timezone.utc)
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO snapshots (ts, payload) VALUES (?, ?)",
                (ts.isoformat(), json.dumps(payload, ensure_ascii=True, separators=(",", ":"))),
            )
            conn.commit()

    def get_events(
        self,
        *,
        limit: int = 100,
        entity_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT ts, plant_id, entity_id, type, payload
            FROM event_logs
            WHERE 1=1
        """
        params: list[Any] = []
        if entity_id:
            sql += " AND entity_id = ?"
            params.append(entity_id)
        if event_type:
            sql += " AND type = ?"
            params.append(event_type)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            {
                "timestamp": row["ts"],
                "plant_id": row["plant_id"],
                "entity_id": row["entity_id"],
                "type": row["type"],
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]

    def get_latest_states(self, *, limit: int = 100, plant_id: Optional[str] = None) -> list[dict[str, Any]]:
        sql = """
            SELECT ts, plant_id, entity_id, state
            FROM state_history
            WHERE 1=1
        """
        params: list[Any] = []
        if plant_id:
            sql += " AND plant_id = ?"
            params.append(plant_id)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            {
                "timestamp": row["ts"],
                "plant_id": row["plant_id"],
                "entity_id": row["entity_id"],
                "state": json.loads(row["state"]),
            }
            for row in rows
        ]

    def get_latest_snapshot(self) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT ts, payload
                FROM snapshots
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return {"timestamp": row["ts"], "payload": json.loads(row["payload"])}
