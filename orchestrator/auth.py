"""
orchestrator/auth.py
JWT Authentication & user-scoped session management for AdvocAI.
Issue #9 — Backend: Add JWT authentication and user-scoped sessions
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production-use-a-long-random-string")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS: int = 24

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = ACCESS_TOKEN_EXPIRE_HOURS * 3600


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Return the user email (subject) or raise HTTPException."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: Optional[str] = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return sub
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# DB helpers (thin wrappers — swap with your real DB layer)
# ---------------------------------------------------------------------------


def _get_db_connection():
    """Return a psycopg2 connection using POSTGRES_URL env var."""
    import psycopg2
    import psycopg2.extras

    url = os.getenv("POSTGRES_URL")
    if not url:
        raise RuntimeError("POSTGRES_URL env var not set")
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def _get_user_by_email(email: str) -> Optional[dict]:
    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cur.fetchone()
    finally:
        conn.close()


def _create_user(email: str, hashed_password: str) -> dict:
    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, hashed_password) VALUES (%s, %s) RETURNING *",
                (email, hashed_password),
            )
            user = cur.fetchone()
            conn.commit()
            return user
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Dependency: get current authenticated user
# ---------------------------------------------------------------------------


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency — attach to any endpoint that requires auth."""
    email = decode_access_token(token)
    user = _get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return dict(user)


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegisterRequest):
    """Register a new user and return a JWT."""
    if _get_user_by_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    hashed = hash_password(body.password)
    _create_user(body.email, hashed)
    token = create_access_token(subject=body.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """Authenticate with email + password, return JWT (24 h expiry)."""
    user = _get_user_by_email(form.username)  # OAuth2 form uses 'username' field
    if not user or not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user["email"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user
