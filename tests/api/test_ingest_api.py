import pytest
import sqlite3

from httpx import AsyncClient, ASGITransport
from api.ingest.main import app
from api.ingest.sinks.sqlite_async import AsyncSqliteSink

from api.ingest.main import app, event_sink


@pytest.mark.asyncio
async def test_event_post_success(monkeypatch):
    def dummy_handler(event):
        pass  # simulate success

    monkeypatch.setattr(event_sink, "handle_rf_events", dummy_handler)

    valid_event = {"event_type": "start_test", "name": "Test Example"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/event", json=valid_event)
        assert response.status_code == 200
        assert response.json()["received"] is True


# Testdata
@pytest.fixture
def test_event():
    return {"event_type": "log_message", "level": "INFO", "message": "Test log"}

@pytest.mark.asyncio
async def test_log_post_success(test_event):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/log", json=test_event)
        assert response.status_code == 200
        assert response.json()["received"] is True

@pytest.mark.asyncio
async def test_log_post_missing_event_type():
    bad_event = {"foo": "bar"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/log", json=bad_event)
        assert response.status_code == 400
        assert response.json() == {"error": "Missing event_type for /log"}

