from fastapi.testclient import TestClient
from api.viewer.app_factory import create_app
from shared.helpers.config_loader import load_config
import pytest
from datetime import datetime, timezone, timedelta

class DummyReader:
    def __init__(self):
        now = datetime.now(timezone.utc)
        self._events = [
            {
                "event_type": "start_suite",
                "starttime": (now - timedelta(seconds=360)).isoformat()
            },
            {
                "event_type": "log_message",
                "message": "Test message",
                "level": "INFO"
            }
        ]
        self._logs = [{"level": "INFO", "message": "Dummy log"}]
        self._cleared = False

    def get_events(self):
        return [] if self._cleared else self._events

    def get_app_logs(self):
        return self._logs

    def clear_events(self):
        self._cleared = True

@pytest.fixture
def client():
    config = load_config()
    app = create_app(config)
    app.state.event_reader = DummyReader()
    yield TestClient(app)



def test_get_applog(client):
    response = client.get("/applog")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["message"] == "Dummy log"


def test_get_events(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["event_type"] == "start_suite"


def test_clear_events(client):
    # Eerst even checken dat events er zijn
    pre = client.get("/events")
    assert len(pre.json()) > 0

    response = client.get("/events/clear", follow_redirects=True)
    assert response.status_code == 200
    assert response.url.path == "/events"

    post = client.get("/events")
    assert post.status_code == 200
    assert post.json() == []


def test_get_elapsed_time(client):
    response = client.get("/elapsed")
    assert response.status_code == 200
    assert "elapsed" in response.json()
    assert isinstance(response.json()["elapsed"], str)


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "RealtimeResults API is running"
    assert "/events" in "".join(data["endpoints"])


def test_favicon(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 204
