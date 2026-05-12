import pytest
from unittest.mock import MagicMock
from models import UserRole
from database import SessionLocal
from models import User

def test_access_denied_for_regular_user(client, token):
    
    response = client.patch(
        "/users/avatar",
        files={"file": ("test.png", b"fake-binary-data", "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have enough permissions"

def test_redis_cache_logic_called(client, token):
    
    from database import redis_client
    
    
    redis_client.get.reset_mock()
    
    
    client.get("/contacts/", headers={"Authorization": f"Bearer {token}"})
    
    
    assert redis_client.get.called
    
    args, _ = redis_client.get.call_args
    assert "user:" in args[0]

def test_register_duplicate_user(client):
    user_data = {"username": "duplicate", "email": "dup@test.com", "password": "password"}
    client.post("/auth/register", json=user_data) # Перший раз
    res = client.post("/auth/register", json=user_data) # Другий раз
    assert res.status_code == 409
    assert res.json()["detail"] == "User with this email already exists"