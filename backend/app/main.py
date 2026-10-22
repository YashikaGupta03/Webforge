from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, audit, auth, departments, issues, notifications
from app.core.config import settings

app = FastAPI(title="CivicSense API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(issues.router, prefix="/api/issues", tags=["Issues"])
app.include_router(departments.router, prefix="/api/departments", tags=["Departments"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}