import pytest
from unittest.mock import patch

def test_register_user(client):
    
    with patch("main.send_email", return_value=True):
        response = client.post("/auth/register", json={
            "username": "tester_new",
            "email": "tester_new@example.com",
            "password": "password123"
        })
        assert response.status_code == 201

def test_login_user(client, token):
    
    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_contact(client, token):
    response = client.post(
        "/contacts/",
        json={
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "email": "ivan@test.com",
            "phone": "123456",
            "birthday": "1990-01-01"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    return response.json()["id"]

def test_update_contact(client, token):
    
    res = client.post("/contacts/", json={
        "first_name": "Old", "last_name": "Name", "email": "old@t.com", 
        "phone": "000", "birthday": "2000-01-01"
    }, headers={"Authorization": f"Bearer {token}"})
    cid = res.json()["id"]

    response = client.put(
        f"/contacts/{cid}",
        json={
            "first_name": "NewName", "last_name": "Name", "email": "old@t.com",
            "phone": "111", "birthday": "2000-01-01"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "NewName"

def test_delete_contact(client, token):
    
    res = client.post("/contacts/", json={
        "first_name": "Delete", "last_name": "Me", "email": "del@t.com", 
        "phone": "000", "birthday": "2000-01-01"
    }, headers={"Authorization": f"Bearer {token}"})
    cid = res.json()["id"]

    response = client.delete(f"/contacts/{cid}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Contact deleted"

def test_search_contacts(client, token):
    
    response = client.get("/contacts/search/?query=Ivan", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_verify_email_error(client):
    
    response = client.get("/auth/verify?token=wrong_token")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid token"

def test_get_birthdays(client, token):
    response = client.get("/contacts/birthdays/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200




