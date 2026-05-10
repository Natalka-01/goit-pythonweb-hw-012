from datetime import datetime, timedelta
from typing import Optional
import os
import secrets
import logging

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy import exc
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Імпорти вашого проекту
from database import get_db, engine, Base
from models import Contact as ContactModel, User, UserRole
import schemas  # Додано імпорт схем цілком
from crud import (
    get_contacts, get_contact, create_contact, update_contact, delete_contact,
    search_contacts, get_upcoming_birthdays, get_user_by_email, get_user_by_username,
    create_user, update_user_avatar, confirm_user_email, get_user_by_verification_token
)
import auth  # Імпортуємо модуль auth цілком
from auth import authenticate_user, create_access_token, get_current_user, get_password_hash, RoleChecker
from email_service import send_email

# --- Налаштування логування та оточення ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
app = FastAPI(title="Contacts API")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(SlowAPIMiddleware)

# Створюємо роутер для авторизації
auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/register", response_model=schemas.User, status_code=201)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=409, detail="User with this email already exists")
    
    verification_token = secrets.token_urlsafe(32)
    new_user = create_user(db, user, verification_token=verification_token)
    
    subject = "Email Verification"
    body = f"Verify your email: http://localhost:8000/auth/verify?token={verification_token}"
    send_email(new_user.email, subject, body)
    
    return new_user

@auth_router.get("/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = get_user_by_verification_token(db, token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    confirm_user_email(db, user.id)
    return {"message": "Email verified successfully"}

@auth_router.post("/login", response_model=schemas.Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user or not user.confirmed:
        raise HTTPException(status_code=401, detail="Invalid credentials or email not verified")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

    
@auth_router.post("/request-reset")
async def request_reset(body: schemas.RequestEmail, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user:
        token = auth.create_reset_token(user.email)
        user.reset_token = token
        db.commit()
        reset_link = f"http://localhost:8000/auth/reset-password?token={token}"
        send_email(user.email, "Password Reset", f"Reset your password: {reset_link}")
    return {"message": "If the email exists, a reset link has been sent."}

@auth_router.post("/reset-password")
async def reset_password(body: schemas.PasswordReset, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email, User.reset_token == body.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Token already used or invalid")

    user.hashed_password = get_password_hash(body.new_password)
    user.reset_token = None
    db.commit()
    return {"message": "Password updated successfully"}


@app.get("/users/me", response_model=schemas.User)
@limiter.limit("10/minute")
def read_users_me(request: Request, current_user: User = Depends(get_current_user)):
    return current_user

@app.patch("/users/avatar", response_model=schemas.User, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
def update_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = cloudinary.uploader.upload(file.file, public_id=f"avatars/{current_user.username}")
        avatar_url = result.get("url")
        return update_user_avatar(db, current_user.id, avatar_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(auth_router)

@app.get("/contacts/", response_model=list[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieve a list of contacts for the current user.

    Args:
        skip: Number of contacts to skip.
        limit: Maximum number of contacts to return.
        db: The database session.
        current_user: The currently authenticated user.

    Returns:
        A list of contact objects.
    """
    contacts = get_contacts(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return contacts

@app.get("/contacts/{contact_id}", response_model=schemas.Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get details of a specific contact by ID.

    Args:
        contact_id: The unique ID of the contact.
        db: The database session.
        current_user: The currently authenticated user.

    Returns:
        The contact object.
    """
    db_contact = get_contact(db=db, contact_id=contact_id, user_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.post("/contacts/", response_model=schemas.Contact, status_code=201)
def create_new_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a new contact for the current user.

    Args:
        contact: The contact data to create.
        db: The database session.
        current_user: The currently authenticated user.

    Returns:
        The created contact object.
    """
    return create_contact(db=db, contact=contact, user_id=current_user.id)

@app.put("/contacts/{contact_id}", response_model=schemas.Contact)
def update_existing_contact(contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Update an existing contact's information.

    Args:
        contact_id: The unique ID of the contact to update.
        contact: The updated contact data.
        db: The database session.
        current_user: The currently authenticated user.

    Returns:
        The updated contact object.
    """
    db_contact = update_contact(db=db, contact_id=contact_id, contact=contact, user_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.delete("/contacts/{contact_id}")
def delete_existing_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Delete a contact by its ID.

    Args:
        contact_id: The unique ID of the contact to delete.
        db: The database session.
        current_user: The currently authenticated user.

    Returns:
        A success message.
    """
    db_contact = delete_contact(db=db, contact_id=contact_id, user_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted"}

@app.get("/contacts/search/", response_model=list[schemas.Contact])
def search_contacts_endpoint(query: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Search for contacts by a query string.

    Args:
        query: The search term (name, email, etc.).
        db: The database session.
        current_user: The currently authenticated user.

    Returns:
        A list of contacts matching the query.
    """
    contacts = search_contacts(db=db, query=query, user_id=current_user.id)
    return contacts

@app.get("/contacts/birthdays/", response_model=list[schemas.Contact])
def get_birthdays(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get a list of contacts with upcoming birthdays.

    Args:
        db: The database session.
        current_user: The currently authenticated user.

    Returns:
        A list of contacts having birthdays in the next 7 days.
    """
    contacts = get_upcoming_birthdays(db=db, user_id=current_user.id)
    return contacts
