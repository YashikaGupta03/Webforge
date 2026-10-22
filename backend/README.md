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

The migration inserts departments and twelve clearly marked placeholder hostel records; replace those with verified MANIT data before production. Provision further accounts through the admin-only `POST /api/auth/users` endpoint or the CLI. There is no public registration endpoint.

## Run the development server

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

Check `http://127.0.0.1:8000/health`; interactive API documentation is available at `http://127.0.0.1:8000/docs`. The Vite frontend proxies `/api` to this server.

When the Vite frontend and backend are both running in development mode, the frontend opens a local demo student dashboard automatically. The backend creates a `LOCAL-DEMO-STUDENT` account on first use. Its token endpoint is restricted to development mode and loopback clients; production deployments must use scholar-number sign-in.

## Current endpoints

- `POST /api/auth/login`, `GET /api/auth/me`, administrator-only `POST /api/auth/users`
- `GET/POST /api/issues`, `POST /api/issues/chat`, `PATCH /api/issues/{token}/status`
- `PATCH /api/issues/{token}/assignment`, `POST /api/issues/{token}/duplicates`
- `GET /api/departments`, `GET /api/departments/hostels`, `GET /api/departments/{id}/staff`
- `GET /api/notifications`, `PATCH /api/notifications/{id}`
- `GET /api/audit`, `GET /api/analytics/summary`

All complaint and administration routes require a bearer token. Students see only their own complaints; wardens are limited to their configured hostel; department staff see assigned work. Seed a Department Staff account for each assignment target before assigning work.

## Tests

```bash
pytest
```
