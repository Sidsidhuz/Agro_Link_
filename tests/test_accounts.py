from fastapi.testclient import TestClient
import database
import main


def test_versioned_accounts_share_existing_routes(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'accounts.db')
    with TestClient(main.app) as client:
        payload = {'username': 'Test Farmer', 'phone': '9999999999', 'password': 'test-password'}
        response = client.post('/api/v1/register', json=payload)
        assert response.status_code == 201
        assert 'password_hash' not in response.json()
        assert client.get('/api/me').json()['id'] == response.json()['id']
        assert client.post('/api/v1/register', json=payload).status_code == 409
        assert client.patch('/api/v1/me', json={'username': 'Updated Farmer', 'latitude': 12}).status_code == 422
        assert client.patch('/api/v1/me', json={'username': 'Updated Farmer', 'latitude': 12, 'longitude': 75}).status_code == 200
        client.post('/api/logout')
        assert client.get('/api/v1/me').status_code == 401
        assert client.post('/api/login', json={'phone': payload['phone'], 'password': payload['password']}).status_code == 200
        assert client.get('/api/v1/me').json()['username'] == 'Updated Farmer'
