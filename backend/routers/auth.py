"""backend/routers/auth.py — Login, signup, token refresh"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from backend.auth import create_access_token, get_current_user
from backend.db import Database
from backend.deps import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str
    password: str
    confirm_password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        if len(v) < 2:
            raise ValueError("Username must be at least 2 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v):
        if not v or len(v) < 4:
            raise ValueError("Password must be at least 4 characters")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserResponse(BaseModel):
    username: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Database = Depends(get_db)):
    username = body.username.capitalize()

    if not db.user_exists(username):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Username not found")

    if not db.check_user_password(username, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect password")

    token = create_access_token(username)
    return TokenResponse(access_token=token, username=username)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: Database = Depends(get_db)):
    username = body.username.strip().capitalize()

    if db.user_exists(username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Username '{username}' already exists")

    if body.password != body.confirm_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Passwords do not match")

    db.add_user(username, body.password)
    token = create_access_token(username)
    return TokenResponse(access_token=token, username=username)


@router.get("/me", response_model=UserResponse)
def me(username: str = Depends(get_current_user)):
    """Returns the currently authenticated user. Used by the frontend on startup."""
    return UserResponse(username=username)


@router.get("/users", response_model=list[str])
def list_users(
    db: Database = Depends(get_db),
    _: str = Depends(get_current_user),  # Must be logged in
):
    """List all usernames (needed for transfer destination selector)."""
    return db.get_usernames()
