"""
orchestrator/auth/router.py
JWT authentication endpoints for AdvocAI (#9)

Endpoints:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me        (protected — requires Bearer token)
  POST /api/auth/logout    (client-side token drop, but useful for audit log later)
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import bcrypt
import jwt
from pydantic import BaseModel, EmailStr

from .db import get_user_by_email, create_user, UserRecord
from .config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer_scheme = HTTPBearer()


# ─── Pydantic schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ─── Helpers ───────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ─── Dependency: current user ──────────────────────────────────────────────────

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> UserRecord:
    payload = decode_token(credentials.credentials)
    user = await get_user_by_email(payload["email"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    existing = await get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    user = await create_user(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
    )

    token = create_access_token(str(user.id), user.email)
    return TokenResponse(
        access_token=token,
        user={"id": str(user.id), "name": user.name, "email": user.email},
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = await get_user_by_email(body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(str(user.id), user.email)
    return TokenResponse(
        access_token=token,
        user={"id": str(user.id), "name": user.name, "email": user.email},
    )


@router.get("/me")
async def me(current_user: Annotated[UserRecord, Depends(get_current_user)]):
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    # Token is stateless — client drops it. This endpoint exists for future
    # token-blocklist / audit-log integration.
    return
