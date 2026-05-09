# FastAPI Contacts API

REST API for contacts with JWT auth, email verification, Cloudinary avatar upload, and PostgreSQL.

## Features

- User registration and login with JWT access tokens
- Email verification for new users
- User-specific contact CRUD operations
- Search contacts by first name, last name, or email
- Upcoming birthdays query
- Cloudinary avatar upload
- Rate limit for `/users/me`
- CORS enabled
- Docker Compose support

## Requirements

- Python 3.12+
- Docker and Docker Compose (recommended)
- `.env` file with secrets

## Setup

1. Copy example env file:

```bash
copy .env.example .env
```

2. Update `.env` 

3. Start services with Docker Compose:

```bash
docker compose up -d --build
```

4. Run migrations inside the `web` container or locally:

```bash
docker compose exec web alembic upgrade head
```

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Main endpoints

- `POST /auth/register` - register user
- `GET /auth/verify?token=...` - verify email
- `POST /auth/login` - login and get `access_token`
- `GET /users/me` - current user profile
- `PATCH /users/avatar` - upload user avatar
- `GET /contacts/` - list user contacts
- `GET /contacts/{contact_id}` - get contact
- `POST /contacts/` - create contact
- `PUT /contacts/{contact_id}` - update contact
- `DELETE /contacts/{contact_id}` - delete contact
- `GET /contacts/search/?query=...` - search user contacts
- `GET /contacts/birthdays/` - upcoming birthdays

## API docs

Open `http://localhost:8000/docs` after the server starts.
