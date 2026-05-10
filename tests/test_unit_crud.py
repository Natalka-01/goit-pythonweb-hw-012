import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from crud import (
    get_contacts, create_contact, get_contact, 
    update_contact, delete_contact, search_contacts
)
from models import Contact
from schemas import ContactCreate, ContactUpdate

@pytest.fixture
def db():
    return MagicMock(spec=Session)

def test_get_contacts(db):
    # Setup Mock
    mock_contacts = [MagicMock(spec=Contact), MagicMock(spec=Contact)]
    db.query().filter().offset().limit().all.return_value = mock_contacts
    
    # Call
    result = get_contacts(db, user_id=1)
    
    # Assert
    assert len(result) == 2
    db.query.assert_called()

def test_create_contact(db):
    # Setup
    contact_data = ContactCreate(
        first_name="John", last_name="Doe", 
        email="john@example.com", phone="123456", birthday="1990-01-01"
    )
    
    # Call
    result = create_contact(db, contact_data, user_id=1)
    
    # Assert
    assert result.first_name == "John"
    assert db.add.called
    assert db.commit.called
    assert db.refresh.called

def test_search_contacts(db):
    # Setup
    db.query().filter().all.return_value = [MagicMock(spec=Contact)]
    
    # Call
    result = search_contacts(db, query="John", user_id=1)
    
    # Assert
    assert len(result) == 1
    db.query.assert_called()

def test_delete_contact_found(db):
    # Setup
    mock_contact = MagicMock(spec=Contact)
    db.query().filter().first.return_value = mock_contact
    
    # Call
    result = delete_contact(db, contact_id=1, user_id=1)
    
    # Assert
    assert result == mock_contact
    assert db.delete.called
    assert db.commit.called