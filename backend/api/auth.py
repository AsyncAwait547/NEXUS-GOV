"""JWT Authentication & Role-Based Access Control (RBAC)."""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from config import settings

logger = logging.getLogger("nexus.auth")

# ── Security Scheme ──
security = HTTPBearer(auto_error=False)


# ── Role Definitions ──
class Role:
    ADMIN = "ADMIN"
    FIRE_CHIEF = "FIRE_CHIEF"
    GRID_MANAGER = "GRID_MANAGER"
    TRAFFIC_CONTROLLER = "TRAFFIC_CONTROLLER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"

    ALL_ROLES = [ADMIN, FIRE_CHIEF, GRID_MANAGER, TRAFFIC_CONTROLLER, OPERATOR, VIEWER]

    # Role → allowed override domains
    DOMAIN_ACCESS = {
        ADMIN: ["*"],
        FIRE_CHIEF: ["EMERGENCY", "HYDROLOGY"],
        GRID_MANAGER: ["ENERGY_GRID"],
        TRAFFIC_CONTROLLER: ["MOBILITY"],
        OPERATOR: ["EMERGENCY", "HYDROLOGY", "MOBILITY", "ENERGY_GRID"],
        VIEWER: [],
    }


# ── Models ──
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    expires_in: int


class UserInfo(BaseModel):
    username: str
    role: str
    full_name: str


# ── Default Users (seeded on startup) ──
DEFAULT_USERS = {
    "admin": {
        "password": "nexus2026",
        "role": Role.ADMIN,
        "full_name": "System Administrator",
    },
    "fire_chief": {
        "password": "fire2026",
        "role": Role.FIRE_CHIEF,
        "full_name": "Fire Chief — GHMC",
    },
    "grid_manager": {
        "password": "grid2026",
        "role": Role.GRID_MANAGER,
        "full_name": "Grid Manager — TSSPDCL",
    },
    "traffic_ctrl": {
        "password": "traffic2026",
        "role": Role.TRAFFIC_CONTROLLER,
        "full_name": "Traffic Controller — Hyderabad Traffic Police",
    },
    "operator": {
        "password": "ops2026",
        "role": Role.OPERATOR,
        "full_name": "Command Center Operator",
    },
    "viewer": {
        "password": "view2026",
        "role": Role.VIEWER,
        "full_name": "Dashboard Viewer",
    },
}


# ── JWT Token Functions ──

def create_access_token(username: str, role: str) -> str:
    """Create a JWT access token."""
    try:
        from jose import jwt
    except ImportError:
        from jose import jwt

    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "nexus-gov",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        from jose import jwt, JWTError

        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except Exception:
        return None


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user against default user store."""
    user = DEFAULT_USERS.get(username)
    if not user:
        return None

    # In production, use passlib.context.CryptContext for bcrypt hashing
    if user["password"] != password:
        return None

    return {
        "username": username,
        "role": user["role"],
        "full_name": user["full_name"],
    }


# ── FastAPI Dependencies ──

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Extract current user from JWT token. Returns None for unauthenticated requests."""
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload:
        return None

    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        return None

    return {"username": username, "role": role}


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Require authentication — raises 401 if not authenticated."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"username": payload["sub"], "role": payload["role"]}


def require_role(*allowed_roles: str):
    """Factory: require specific roles for access."""

    def role_checker(user: dict = Depends(require_auth)) -> dict:
        if user["role"] not in allowed_roles and Role.ADMIN not in allowed_roles or (
            user["role"] != Role.ADMIN and user["role"] not in allowed_roles
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}. Your role: {user['role']}.",
            )
        return user

    return role_checker
