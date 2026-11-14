from fastapi import FastAPI

app = FastAPI(
    title="Absence & Capacity API",
    description="Backend for the Project 3 Absence & Capacity application.",
    version="0.1.0",
)


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
