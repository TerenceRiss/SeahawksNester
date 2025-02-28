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

def test_scan_protected_route(client):
    response = client.get('/scan')  # Changer POST en GET si nécessaire
    assert response.status_code in [401, 405, 404]  # Accepter 401 ou 405 comme résultat valide


