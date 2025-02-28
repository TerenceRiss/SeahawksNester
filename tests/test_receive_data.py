import pytest
import jwt
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def valid_token():
    token = jwt.encode({"username": "testuser"}, app.config["SECRET_KEY"], algorithm="HS256")
    return token

def test_receive_data_without_token(client):
    response = client.post('/receive-data', json={})
    assert response.status_code == 401
    assert response.json["message"] == "Token manquant !"

def test_receive_data_with_valid_token(client, valid_token):
    headers = {"x-access-token": valid_token}
    response = client.post('/receive-data', json={"hosts": []}, headers=headers)
    assert response.status_code == 200
    assert response.json["status"] == "success"
