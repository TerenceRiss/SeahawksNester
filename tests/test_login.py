import pytest
import sqlite3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_success(client):
    client.post('/register', json={"username": "testuser", "password": "testpass"})
    response = client.post('/login', json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert "token" in response.json

def test_login_invalid_credentials(client):
    response = client.post('/login', json={"username": "wronguser", "password": "wrongpass"})
    assert response.status_code == 401
    assert response.json["message"] == "Identifiants incorrects"
