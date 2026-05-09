from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import date, timedelta
from models import Contact, User
from schemas import ContactCreate, ContactUpdate, UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Contact).filter(Contact.user_id == user_id).offset(skip).limit(limit).all()

def get_contact(db: Session, contact_id: int, user_id: int):
    return db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()

def create_contact(db: Session, contact: ContactCreate, user_id: int):
    db_contact = Contact(**contact.dict(), user_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def update_contact(db: Session, contact_id: int, contact: ContactUpdate, user_id: int):
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if db_contact:
        for key, value in contact.dict().items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int, user_id: int):
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def search_contacts(db: Session, query: str, user_id: int):
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
    today = date.today()
    next_week = today + timedelta(days=7)
    return db.query(Contact).filter(
        and_(
            Contact.user_id == user_id,
            Contact.birthday >= today,
            Contact.birthday <= next_week
        )
    ).all()

# User CRUD
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate, avatar: str = None, verification_token: str = None):
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
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.avatar = avatar
        db.commit()
        db.refresh(db_user)
    return db_user

def confirm_user_email(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.confirmed = True
        db_user.verification_token = None 
        db.commit()
        db.refresh(db_user)
    return db_user

def get_user_by_verification_token(db: Session, token: str):
    return db.query(User).filter(User.email_verification_token == token).first()
