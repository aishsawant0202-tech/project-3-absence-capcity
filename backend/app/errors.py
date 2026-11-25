"""Error responses in the API contract v2 format (section 1.2), for every endpoint:

    {"error": {"code": "FORBIDDEN", "message": "Not allowed.", "details": {}}}

Raise `ApiError(status, code, message)` in routers, services and dependencies.
`register_error_handlers(app)` in main.py turns these, FastAPI's validation errors and any
HTTPException into that format, so the frontend can always read `error.code`.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

# Codes from the contract (section 1.2) plus the team codes; keep in sync with api_contracts_v2.md
VALIDATION_ERROR = "VALIDATION_ERROR"
UNAUTHENTICATED = "UNAUTHENTICATED"
FORBIDDEN = "FORBIDDEN"
NOT_FOUND = "NOT_FOUND"
TEAM_NAME_TAKEN = "TEAM_NAME_TAKEN"
ALREADY_TEAM_LEAD = "ALREADY_TEAM_LEAD"
# Employee codes (Member 3)
EMAIL_TAKEN = "EMAIL_TAKEN"                 # 409: another employee already has this email
EMPLOYEE_REF_TAKEN = "EMPLOYEE_REF_TAKEN"   # 409: another employee already has this reference
TEAM_INACTIVE = "TEAM_INACTIVE"             # 409: employees cannot be added to an inactive team

# Code for an HTTPException raised without ApiError (e.g. 404 for an unknown URL)
_CODE_BY_STATUS = {400: VALIDATION_ERROR, 401: UNAUTHENTICATED, 403: FORBIDDEN, 404: NOT_FOUND}


class ApiError(Exception):
    """An error the API returns on purpose, e.g. ApiError(409, TEAM_NAME_TAKEN, "A team with this name already exists.")."""

    def __init__(self, status_code: int, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


class ErrorBody(BaseModel):
    code: str = Field(examples=["FORBIDDEN"])
    message: str = Field(examples=["Not allowed."])
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Shape of every error response. Used in the routers' `responses=` so Swagger shows it."""

    error: ErrorBody


def _response(status_code: int, code: str, message: str, details: dict[str, Any] | None = None) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details or {}))
    return JSONResponse(status_code=status_code, content=body.model_dump())


async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
    return _response(exc.status_code, exc.code, exc.message, exc.details)


async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Wrong JSON / missing or invalid field -> 400 VALIDATION_ERROR with one entry per field."""
    fields = []
    for err in exc.errors():
        loc = [str(part) for part in err.get("loc", ()) if part not in ("body", "query", "path", "header")]
        fields.append({
            "field": ".".join(loc),
            "message": str(err.get("msg", "Invalid value.")).removeprefix("Value error, "),
        })
    return _response(400, VALIDATION_ERROR, "Some fields are missing or invalid.", {"fields": fields})


async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _CODE_BY_STATUS.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return _response(exc.status_code, code, message)


def _openapi_without_422(app: FastAPI):
    """FastAPI documents a 422 response on every endpoint; we answer 400 instead, so drop it from /docs."""
    default_openapi = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            schema = default_openapi()
            for path in schema.get("paths", {}).values():
                for operation in path.values():
                    operation.get("responses", {}).pop("422", None)
            for name in ("HTTPValidationError", "ValidationError"):
                schema.get("components", {}).get("schemas", {}).pop(name, None)
            app.openapi_schema = schema
        return app.openapi_schema

    return openapi


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.openapi = _openapi_without_422(app)
