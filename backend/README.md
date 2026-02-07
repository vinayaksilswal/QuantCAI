## Backend setup (production-ish)

- **Environment variables** (required):
  - `DATABASE_URL` – PostgreSQL connection string.
  - `AUTH_SECRET_KEY` – strong random secret for JWT signing.
  - `ALLOWED_ORIGINS` – comma-separated list of frontend origins (e.g. `https://app.example.com,https://admin.example.com`).
  - `GOOGLE_CLIENT_ID` – OAuth client ID for Google sign-in.
  - (optional) `ACCESS_TOKEN_MINUTES`, `REFRESH_TOKEN_MINUTES`, `AUTH_ALGORITHM`.

- **Initial schema / migrations**:
  - Run `python migrate_db.py` from the `backend` directory to create/update tables based on the SQLAlchemy models.

- **Running the API**:
  - Install deps: `pip install -r requirements.txt`.
  - Start server (example): `uvicorn main:app --host 0.0.0.0 --port 8000`.

