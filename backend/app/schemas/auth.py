
from pydantic import BaseModel, Field, ConfigDict


class LoginRequest(BaseModel):
    """Credentials submitted by a user."""

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
    must_change_password: bool


class CurrentUserResponse(BaseModel):
    """Information about the authenticated user."""

    id: int
    employee_id: int
    username: str
    role: str
    status: str
    must_change_password: bool
    first_name: str
    last_name: str
    email: str
