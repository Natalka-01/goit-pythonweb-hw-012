from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import exc
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import cloudinary
import cloudinary.uploader
import os
import logging
from database import get_db, engine, Base
from models import Contact, User
from schemas import ContactCreate, ContactUpdate, Contact, UserCreate, User, Token
from crud import (
    get_contacts, get_contact, create_contact, update_contact, delete_contact,
    search_contacts, get_upcoming_birthdays, get_user_by_email, get_user_by_username,
    create_user, update_user_avatar, confirm_user_email, get_user_by_verification_token
)
from auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from email_service import send_email
import secrets
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

app = FastAPI(title="Contacts API", description="API for managing contacts")



# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Auth routes
@app.post("/auth/register", response_model=User, status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=409, detail="User with this email already exists")
    if get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=409, detail="User with this username already exists")

    verification_token = secrets.token_urlsafe(32)
    try:
        new_user = create_user(db, user, verification_token=verification_token)
        
        subject = "Email Verification"
        body = f"Please verify your email: http://localhost:8000/auth/verify?token={verification_token}"
        
        
        email_sent = send_email(new_user.email, subject, body)
        if not email_sent:
            logger.warning(f"Verification email could not be sent to {new_user.email}") 
            
        return new_user
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")

@app.get("/auth/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = get_user_by_verification_token(db, token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    confirm_user_email(db, user.id)
    return {"message": "Email verified successfully"}

@app.post("/auth/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=401,
            detail="Email not verified",
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Users routes
@app.get("/users/me", response_model=User)
@limiter.limit("10/minute")
def read_users_me(request: Request, current_user: User = Depends(get_current_user)):
    return current_user

@app.patch("/users/avatar", response_model=User)
def update_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = cloudinary.uploader.upload(file.file, public_id=f"avatars/{current_user.username}")
        avatar_url = result.get("url")
        
        if not avatar_url:
            raise HTTPException(status_code=500, detail="Failed to get URL from Cloudinary")
            
        updated_user = update_user_avatar(db, current_user.id, avatar_url)
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

# Contacts routes
@app.get("/contacts/", response_model=list[Contact])
def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contacts = get_contacts(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return contacts

@app.get("/contacts/{contact_id}", response_model=Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_contact = get_contact(db=db, contact_id=contact_id, user_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.post("/contacts/", response_model=Contact, status_code=201)
def create_new_contact(contact: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_contact(db=db, contact=contact, user_id=current_user.id)

@app.put("/contacts/{contact_id}", response_model=Contact)
def update_existing_contact(contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_contact = update_contact(db=db, contact_id=contact_id, contact=contact, user_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.delete("/contacts/{contact_id}")
def delete_existing_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_contact = delete_contact(db=db, contact_id=contact_id, user_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted"}

@app.get("/contacts/search/", response_model=list[Contact])
def search_contacts_endpoint(query: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contacts = search_contacts(db=db, query=query, user_id=current_user.id)
    return contacts

@app.get("/contacts/birthdays/", response_model=list[Contact])
def get_birthdays(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contacts = get_upcoming_birthdays(db=db, user_id=current_user.id)
    return contacts