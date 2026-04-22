import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings

log = structlog.get_logger()
settings = get_settings()
_bearer = HTTPBearer()


# ---------------------------------------------------------------------------
# Modelo de usuario autenticado (resultado de validar el JWT)
# ---------------------------------------------------------------------------

@dataclass
class CurrentUser:
    email: str
    name: str
    role: str | None
    permissions: dict

    @property
    def is_admin(self) -> bool:
        return self.role == "ADMIN"

    @property
    def is_viewer(self) -> bool:
        return self.role in ("ADMIN", "VIEWER")


# ---------------------------------------------------------------------------
# Creación de tokens internos
# ---------------------------------------------------------------------------

def create_access_token(
    email: str,
    name: str,
    role: str | None,
    permissions: dict,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": email,
        "name": name,
        "role": role,
        "permissions": permissions,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_expire_days
    )
    payload = {
        "sub": email,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str = "access") -> dict:
    """Decodifica y valida un JWT interno. Lanza HTTPException si es inválido."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != expected_type:
            raise credentials_exception
        if not payload.get("sub"):
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    """Valida el JWT y retorna el usuario actual. No consulta la BD."""
    payload = decode_token(credentials.credentials, expected_type="access")
    return CurrentUser(
        email=payload["sub"],
        name=payload.get("name", payload["sub"]),
        role=payload.get("role"),
        permissions=payload.get("permissions", {}),
    )


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol ADMIN para esta operación",
        )
    return current_user


async def require_viewer(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Permite acceso a ADMIN y VIEWER."""
    if not current_user.is_viewer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado",
        )
    return current_user
