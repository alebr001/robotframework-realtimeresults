import sqlite3
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

class SqliteReader:
    def __init__(self, database_url: str):
        super().__init__()

        # Expect form sqlite:///path/to/file.db
        parsed = urlparse(database_url)
        if parsed.scheme != "sqlite":
            raise ValueError("Invalid sqlite URL")
        # On Windows, netloc may be empty; path includes leading '/'
        self._db_path = parsed.path.lstrip("/") if parsed.path else ":memory:"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_latest_event_id(self, tenant_id: str = "default") -> int:
        with self._connect() as db:
            cur = db.execute(
                "SELECT COALESCE(MAX(id), 0) AS max_id FROM events WHERE tenant_id = ?",
                (tenant_id,)
            )
            row = cur.fetchone()
            return int(row["max_id"]) if row and row["max_id"] is not None else 0

    def get_events_since(self, last_id: int, tenant_id: str = "default") -> List[Dict[str, Any]]:
        with self._connect() as db:
            cur = db.execute(
                """
                SELECT id, event_type, status, starttime, endtime, suite, name, message, tenant_id
                FROM events
                WHERE id > ? AND tenant_id = ?
                ORDER BY id ASC
                """,
                (last_id, tenant_id)
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        
    def clear_events(self, tenant_id: str = "default"):
        with self._connect() as db:
            db.execute("DELETE FROM events WHERE tenant_id = ?", (tenant_id,))
            db.commit()

    def get_app_logs(self, tenant_id: str = "default", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        sql = (
            "SELECT id, timestamp, level, message, event_type, tenant_id "
            "FROM app_logs WHERE tenant_id = ? ORDER BY id DESC"
        )
        params = [tenant_id]
        if limit:
            sql += " LIMIT ?"
            params.append(str(limit))
        with self._connect() as db:
            cur = db.execute(sql, tuple(params))
            rows = cur.fetchall()
            # return newest first -> caller may reverse
            return [dict(r) for r in rows]