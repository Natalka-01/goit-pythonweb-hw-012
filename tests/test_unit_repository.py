import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from crud import get_contacts, create_contact, delete_contact
from models import Contact
from schemas import ContactCreate

@pytest.fixture
def db():
    return MagicMock(spec=Session)

def test_get_contacts(db):
    user_id = 1
    mock_contacts = [MagicMock(spec=Contact), MagicMock(spec=Contact)]
    db.query().filter().offset().limit().all.return_value = mock_contacts
    
    result = get_contacts(db, user_id=user_id)
    
    assert len(result) == 2
    assert result == mock_contacts

def test_create_contact(db):
    user_id = 1
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="123456789",
        birthday="1990-01-01"
    )
    
    result = create_contact(db, contact_data, user_id=user_id)
    
    assert result.first_name == "John"
    assert result.user_id == user_id
    db.add.assert_called_once()
    db.commit.assert_called_once()

def test_delete_contact_not_found(db):
    db.query().filter().first.return_value = None
    result = delete_contact(db, contact_id=999, user_id=1)
    assert result is None