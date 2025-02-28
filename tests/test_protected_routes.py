import pytest
import jwt
from server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def valid_token():
    """ Génère un token JWT valide pour les tests """
    token = jwt.encode({"username": "testuser"}, app.config["SECRET_KEY"], algorithm="HS256")
    return token

def test_protected_route_without_token(client):
    """ Test une route protégée sans fournir de token (doit renvoyer 401) """
    response = client.post('/receive-data', json={})  # Route réellement protégée
    assert response.status_code == 401
    assert response.json["message"] == "Token manquant !"

def test_protected_route_with_invalid_token(client):
    """ Test une route protégée avec un token invalide (doit renvoyer 401 ou 200 si la route n'est pas protégée) """
    headers = {"x-access-token": "invalidtoken"}
    response = client.post('/receive-data', headers=headers, json={})
    assert response.status_code == 401  # Vérifie que le token est bien rejeté

def test_protected_route_with_valid_token(client, valid_token):
    """ Test une route protégée avec un token valide (doit renvoyer 200) """
    headers = {"x-access-token": valid_token}
    response = client.post('/receive-data', headers=headers, json={"hosts": []})
    assert response.status_code == 200  # Vérifie que l'accès est autorisé
    assert response.json["status"] == "success"
