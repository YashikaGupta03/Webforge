from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your route modules
from app.api.routes import issues, auth, departments, analytics, audit, notifications

app = FastAPI(title="CivicSense API", version="1.0.0")

# Enable CORS for the Vite frontend
app.add_middleware(
    CORSMiddleware,
  allow_origins=[
    "http://localhost:5173",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5175",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Register the routers into FastAPI
app.include_router(issues.router, prefix="/api/issues", tags=["Issues / Complaints"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(departments.router, prefix="/api/departments", tags=["Departments"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])