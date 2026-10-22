# CampusAlly Backend

Initial FastAPI backend skeleton. Complaint APIs, authentication, and database models are not implemented yet.

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

Copy `.env.example` to `.env` and set `DATABASE_URL`, `APP_ENVIRONMENT`, and `SECRET_KEY` for your environment. The health endpoint does not require a database connection; database operations will require a valid PostgreSQL URL.

## Run the development server

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

Check `http://127.0.0.1:8000/health` for the basic health response. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.
