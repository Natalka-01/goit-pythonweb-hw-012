import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required in environment")

engine = create_engine(DATABASE_URL, future=True, echo=False, connect_args={"options": "-c client_encoding=utf8"})
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()