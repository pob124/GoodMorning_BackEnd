import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_login():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code in [200, 401]  # 401 for invalid credentials 