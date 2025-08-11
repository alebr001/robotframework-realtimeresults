import asyncio
import json
import logging
from typing import Dict, Set, Any

logger = logging.getLogger("rt.api.viewer.events")

class EventManager:
    """Per-tenant SSE queue manager.
    - _clients: tenant_id -> set(asyncio.Queue)
    - _app_log_clients: tenant_id -> set(asyncio.Queue)
    """
    def __init__(self):
        self._clients: Dict[str, Set[asyncio.Queue]] = {}
        self._app_log_clients: Dict[str, Set[asyncio.Queue]] = {}

    def _bucket(self, bucket: Dict[str, Set[asyncio.Queue]], tenant: str) -> Set[asyncio.Queue]:
        return bucket.setdefault(tenant, set())

    # ---- events ----
    async def add_client(self, tenant: str, q: asyncio.Queue):
        self._bucket(self._clients, tenant).add(q)
        logger.debug(
            "Added event client for tenant %s. Tenants=%d, tenant_clients=%d",
            tenant, len(self._clients), len(self._clients[tenant])
        )

    async def remove_client(self, tenant: str, q: asyncio.Queue):
        self._clients.get(tenant, set()).discard(q)
        logger.debug(
            "Removed event client for tenant %s. Tenants=%d, tenant_clients=%d",
            tenant, len(self._clients), len(self._clients.get(tenant, set()))
        )

    async def broadcast_event(self, tenant: str, event: Dict[str, Any]):
        if tenant not in self._clients:
            return
        payload = f"data: {json.dumps(event)}\n\n"
        disconnected: Set[asyncio.Queue] = set()

        for q in list(self._clients[tenant]):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                # drop oldest item to keep up with live feed
                try:
                    _ = q.get_nowait()
                    q.put_nowait(payload)
                except Exception:
                    logger.warning("Event client queue unhealthy; removing client (tenant=%s)", tenant)
                    disconnected.add(q)

        for q in disconnected:
            self._clients[tenant].discard(q)

    # ---- applogs ----
    async def add_app_log_client(self, tenant: str, q: asyncio.Queue):
        self._bucket(self._app_log_clients, tenant).add(q)
        logger.debug(
            "Added applog client for tenant %s. Tenants=%d, tenant_clients=%d",
            tenant, len(self._app_log_clients), len(self._app_log_clients[tenant])
        )

    async def remove_app_log_client(self, tenant: str, q: asyncio.Queue):
        self._app_log_clients.get(tenant, set()).discard(q)
        logger.debug(
            "Removed applog client for tenant %s. Tenants=%d, tenant_clients=%d",
            tenant, len(self._app_log_clients), len(self._app_log_clients.get(tenant, set()))
        )

    async def broadcast_app_log(self, tenant: str, record: Dict[str, Any]):
        if tenant not in self._app_log_clients:
            return
        payload = f"data: {json.dumps(record)}\n\n"
        disconnected: Set[asyncio.Queue] = set()

        for q in list(self._app_log_clients[tenant]):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                try:
                    _ = q.get_nowait()
                    q.put_nowait(payload)
                except Exception:
                    logger.warning("Applog client queue unhealthy; removing client (tenant=%s)", tenant)
                    disconnected.add(q)

        for q in disconnected:
            self._app_log_clients[tenant].discard(q)

    def get_client_count(self) -> Dict[str, int]:
        total_event = sum(len(s) for s in self._clients.values())
        total_log = sum(len(s) for s in self._app_log_clients.values())
        return {
            "event_clients": total_event,
            "app_log_clients": total_log,
            "event_tenants": len(self._clients),
            "app_log_tenants": len(self._app_log_clients),
        }
