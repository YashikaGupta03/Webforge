# CivicSense Backend

FastAPI/PostgreSQL Phase 1–2 implementation: institute account provisioning, authenticated complaint intake, rule-based text classification, status updates, staff assignment, notifications, and audit events. The classifier is a deterministic bootstrap, not an ML model. Duplicate detection, embeddings, image analysis, geo-clustering, and external email/SMS are not implemented.

## Setup

From the `backend/` directory, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`, replace the placeholder database password and `SECRET_KEY`, and keep `.env` private. `SECRET_KEY` must contain at least 32 bytes; generate one locally with `openssl rand -hex 32`. Start local PostGIS:

```bash
docker compose up -d db
```

Run database migrations and provision the first administrator interactively:

```bash
alembic upgrade head
python -m app.cli create-user --role "Super Admin"
```

The migration inserts departments and twelve clearly marked placeholder hostel records; replace those with verified MANIT data before production. Staff and administrator accounts must be provisioned through the admin-only `POST /api/auth/users` endpoint or the CLI.

Students can create an account at `/signup` with their name, institute email, scholar number, and a password of at least 12 characters. Sign-up stores a password hash in the configured database, assigns the `Student` role, and directs the student to sign in. Email addresses and scholar numbers must be unique.

## Run the development server

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

Check `http://127.0.0.1:8000/health`; interactive API documentation is available at `http://127.0.0.1:8000/docs`. The Vite frontend proxies `/api` to this server.

In Vite development mode, the sign-in page and authenticated top-right dashboard selector offer local demo accounts for Student, Warden, Administrator, Department Staff, or Super Admin. The backend creates each account on first use and returns a normal bearer token, so dashboard data and actions use the configured database. Demo-role sign-in is restricted to `APP_ENVIRONMENT=development` and loopback clients; it is not available in production. PostgreSQL must be running and migrations applied first.

## Current endpoints

- `POST /api/auth/login`, `GET /api/auth/me`, administrator-only `POST /api/auth/users`
- `GET/POST /api/issues`, `POST /api/issues/chat`, `PATCH /api/issues/{token}/status`
- `PATCH /api/issues/{token}/assignment`, `POST /api/issues/{token}/duplicates`
- `GET /api/departments`, `GET /api/departments/hostels`, `GET /api/departments/{id}/staff`
- `GET /api/notifications`, `PATCH /api/notifications/{id}`
- `GET /api/audit`, `GET /api/analytics/summary`

All complaint and administration routes require a bearer token. Students see only their own complaints; wardens are limited to their configured hostel; department staff see assigned work. Seed a Department Staff account for each assignment target before assigning work.yes 

## Tests

```bash
pytest
```
