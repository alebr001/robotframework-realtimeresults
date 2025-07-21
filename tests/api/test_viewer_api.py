import pytest
from api.viewer.main import app
from starlette.testclient import TestClient

def test_api_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200

def test_api_not_found():
    client = TestClient(app)
    response = client.get("/notfound")
    assert response.status_code == 404
