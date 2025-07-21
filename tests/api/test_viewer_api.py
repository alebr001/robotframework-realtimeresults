import pytest
from api.viewer.main import app
from starlette.testclient import TestClient
from unittest.mock import patch

@pytest.fixture(autouse=True, scope="module")
def mock_config_loader():
    with patch("api.viewer.main.load_config", return_value={}):
        yield


def test_api_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200

def test_api_not_found():
    client = TestClient(app)
    response = client.get("/notfound")
    assert response.status_code == 404
