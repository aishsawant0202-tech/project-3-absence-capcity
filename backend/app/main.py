from fastapi import FastAPI

from app.errors import register_error_handlers
from app.routers import teams

app = FastAPI(
    title="Absence & Capacity API",
    description="Backend for the Project 3 Absence & Capacity application.",
    version="0.1.0",
)
register_error_handlers(app)  # every error -> {"error": {"code", "message", "details"}} (contract v2, 1.2)

app.include_router(teams.router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "absence-capacity-api",
    }


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "message": "Absence & Capacity API is running.",
        "docs": "/docs",
    }
