import pytest
import sqlite3

from httpx import AsyncClient, ASGITransport
from api.ingest.main import app
from api.ingest.sinks.sqlite_async import AsyncSqliteSink

from api.ingest.main import app, event_sink


@pytest.mark.asyncio
async def test_event_post_success(monkeypatch, test_event):
    def dummy_handler(event):
        pass  # do nothing, just simulate success

    monkeypatch.setattr(event_sink, "handle_event", dummy_handler)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/event", json=test_event)
        assert response.status_code == 200
        assert response.json()["received"] is True


# Testdata
@pytest.fixture
def test_event():
    return {"event_type": "log_message", "level": "INFO", "message": "Test log"}

@pytest.mark.asyncio
async def test_log_get_info_returns_message():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/log")
        assert response.status_code == 200
        assert "status" in response.json()
        assert "expects POST" in response.json()["status"]

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
        assert "event_type is missing" in response.text

@pytest.mark.asyncio
async def test_sqlite_operational_error(monkeypatch, test_event):
    async def broken_handle_event(self, event):
        raise sqlite3.OperationalError("test failure")

    monkeypatch.setattr(AsyncSqliteSink, "async_handle_event", broken_handle_event)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/log", json=test_event)
        assert response.status_code == 500
        assert "Unexpected error" in response.text
