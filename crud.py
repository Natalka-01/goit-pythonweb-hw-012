from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import date, timedelta
from models import Contact, User
from schemas import ContactCreate, ContactUpdate, UserCreate
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    Retrieve a list of contacts for a specific user with pagination.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user owning the contacts.
        skip (int): The number of contacts to skip.
        limit (int): The maximum number of contacts to return.

    Returns:
        list[Contact]: A list of contact objects.
    """
    return db.query(Contact).filter(Contact.user_id == user_id).offset(skip).limit(limit).all()

def get_contact(db: Session, contact_id: int, user_id: int):
    """
    Retrieve a single contact by its ID and owner ID.

    Args:
        db (Session): The database session.
        contact_id (int): The ID of the contact to retrieve.
        user_id (int): The ID of the user owning the contact.

    Returns:
        Contact | None: The contact object if found, otherwise None.
    """
    return db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()

def create_contact(db: Session, contact: ContactCreate, user_id: int):
    """
    Create a new contact for a user.

    Args:
        db (Session): The database session.
        contact (ContactCreate): The data for the new contact.
        user_id (int): The ID of the user who will own this contact.

    Returns:
        Contact: The created contact object.
    """
    db_contact = Contact(**contact.model_dump(), user_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def update_contact(db: Session, contact_id: int, contact: ContactUpdate, user_id: int):
    """
    Update an existing contact's information.

    Args:
        db (Session): The database session.
        contact_id (int): The ID of the contact to update.
        contact (ContactUpdate): The new data for the contact.
        user_id (int): The ID of the user owning the contact.

    Returns:
        Contact | None: The updated contact object if found, otherwise None.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if db_contact:
        for key, value in contact.model_dump().items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int, user_id: int):
    """
    Remove a contact from the database.

    Args:
        db (Session): The database session.
        contact_id (int): The ID of the contact to delete.
        user_id (int): The ID of the user owning the contact.

    Returns:
        Contact | None: The deleted contact object if found, otherwise None.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def search_contacts(db: Session, query: str, user_id: int):
    """
    Search for contacts by first name, last name, or email.

    Args:
        db (Session): The database session.
        query (str): The search string.
        user_id (int): The ID of the user owning the contacts.

    Returns:
        list[Contact]: A list of matching contact objects.
    """
    return db.query(Contact).filter(
        and_(
            Contact.user_id == user_id,
            or_(
                Contact.first_name.ilike(f"%{query}%"),
                Contact.last_name.ilike(f"%{query}%"),
                Contact.email.ilike(f"%{query}%")
            )
        )
    ).all()

def get_upcoming_birthdays(db: Session, user_id: int):
    """
    Retrieve contacts whose birthdays occur within the next 7 days.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user owning the contacts.

    Returns:
        list[Contact]: A list of contacts with upcoming birthdays.
    """
    today = date.today()
    next_week = today + timedelta(days=7)
    return db.query(Contact).filter(
        and_(
            Contact.user_id == user_id,
            Contact.birthday >= today,
            Contact.birthday <= next_week
        )
    ).all()

# --- User CRUD operations ---

def get_user_by_username(db: Session, username: str):
    """
    Retrieve a user by their username.

    Args:
        db (Session): The database session.
        username (str): The username to search for.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user by their email address.

    Args:
        db (Session): The database session.
        email (str): The email address to search for.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate, avatar: str = None, verification_token: str = None):
    """
    Register a new user in the system with a hashed password.

    Args:
        db (Session): The database session.
        user (UserCreate): The user data for registration.
        avatar (str, optional): The URL for the user's avatar.
        verification_token (str, optional): The token used for email verification.

    Returns:
        User: The newly created user object.
    """
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        avatar=avatar,
        email_verification_token=verification_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_avatar(db: Session, user_id: int, avatar: str):
    """
    Update the avatar URL for a specific user.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.
        avatar (str): The new avatar URL.

    Returns:
        User | None: The updated user object if found, otherwise None.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.avatar = avatar
        db.commit()
        db.refresh(db_user)
    return db_user

def confirm_user_email(db: Session, user_id: int):
    """
    Mark a user's email as confirmed and clear the verification token.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.

    Returns:
        User | None: The updated user object if found, otherwise None.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.confirmed = True
        db_user.email_verification_token = None 
        db.commit()
        db.refresh(db_user)
    return db_user

def get_user_by_verification_token(db: Session, token: str):
    """
    Retrieve a user by their email verification token.

    Args:
        db (Session): The database session.
        token (str): The verification token to search for.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    return db.query(User).filter(User.email_verification_token == token).first()