import pytest
from fastapi.testclient import TestClient
from api.ingest.app_factory import create_app


class DummySink:
    def __init__(self):
        self.handled_events = []

    async def handle_app_log(self, event):
        self.handled_events.append(("log", event))

    async def handle_metric(self, event):
        self.handled_events.append(("metric", event))

    async def handle_rf_events(self, event):
        self.handled_events.append(("event", event))

    async def handle_rf_log(self, event):
        self.handled_events.append(("event/log_message", event))

    async def initialize_database(self):
        pass  # No-op for testing


@pytest.fixture
def client(monkeypatch):
    app = create_app()
    dummy_sink = DummySink()
    app.state.event_sink = dummy_sink
    return TestClient(app), dummy_sink


def test_log_endpoint_valid_event(client):
    client, sink = client
    payload = {"event_type": "app_log", "message": "test log"}
    response = client.post("/log", json=payload)
    assert response.status_code == 200
    assert response.json() == {"received": True}
    assert sink.handled_events[0][0] == "log"


def test_metric_endpoint_valid_event(client):
    client, sink = client
    payload = {"event_type": "metric", "value": 42}
    response = client.post("/metric", json=payload)
    assert response.status_code == 200
    assert sink.handled_events[0][0] == "metric"


def test_event_endpoint_valid_event(client):
    client, sink = client
    payload = {"event_type": "start_test", "name": "Login"}
    response = client.post("/event", json=payload)
    assert response.status_code == 200
    assert sink.handled_events[0][0] == "event"


def test_event_log_message_valid(client):
    client, sink = client
    payload = {"event_type": "log_message", "message": "Something happened"}
    response = client.post("/event/log_message", json=payload)
    assert response.status_code == 200
    assert sink.handled_events[0][0] == "event/log_message"


def test_missing_event_type(client):
    client, _ = client
    response = client.post("/log", json={"foo": "bar"})
    assert response.status_code == 400
    assert "Missing event_type" in response.json()["error"]


def test_invalid_event_type(client):
    client, _ = client
    response = client.post("/metric", json={"event_type": "something_else"})
    assert response.status_code == 400
    assert "Invalid event_type" in response.json()["error"]
