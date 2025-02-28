import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_metrics_access(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b"# HELP scan_requests_total" in response.data
