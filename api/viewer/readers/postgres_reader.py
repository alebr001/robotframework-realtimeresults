from typing import List, Dict, Any, Optional, Mapping, cast
import psycopg2
import psycopg2.extras


class PostgresReader:
    def __init__(self, database_url: str):
        super().__init__()
        self._dsn = database_url

    def _connect(self):
        # RealDictCursor -> rows behave like dicts: row["column"]
        return psycopg2.connect(self._dsn, cursor_factory=psycopg2.extras.RealDictCursor)

    def get_latest_event_id(self, tenant_id: str) -> int:
        sql = "SELECT COALESCE(MAX(id), 0) AS max_id FROM events WHERE tenant_id = %s"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (tenant_id,))
            row = cur.fetchone()
            # Tell the type checker this is a dict-like row
            mrow = cast(Optional[Mapping[str, Any]], row)
            val = mrow["max_id"] if (mrow and mrow["max_id"] is not None) else 0
            return int(val)
        
    def get_events_since(self, last_id: int, tenant_id: str) -> List[Dict[str, Any]]:
        sql = """
            SELECT id, event_type, status, endtime, suite, name, message, tenant_id
            FROM events
            WHERE id > %s AND tenant_id = %s
            ORDER BY id ASC
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (last_id, tenant_id))
            rows = cur.fetchall()  # List[RealDictRow]
            # Return plain dicts (optional but nice for JSON serialization)
            return [dict(r) for r in rows]

    def get_app_logs(self, tenant_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        base_sql = (
            "SELECT id, timestamp, level, message, event_type "
            "FROM app_logs WHERE tenant_id = %s ORDER BY id DESC"
        )
        params = [tenant_id]
        if limit is not None:
            base_sql += " LIMIT %s"
            params.append(str(limit))

        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(base_sql, tuple(params))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
