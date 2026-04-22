import secrets

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.azure import exchange_code_for_token, extract_user_info, get_auth_url
from app.auth.dependencies import (
    CurrentUser,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from app.config import get_settings
from app.database import get_db
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.auth import (
    LoginUrlResponse,
    RefreshRequest,
    TokenResponse,
    UserInfoResponse,
)

log = structlog.get_logger()
settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

async def _resolve_user_role(
    email: str, db: AsyncSession
) -> tuple[str | None, dict]:
    """
    Busca el rol del usuario en BD.
    Si no tiene rol y no existe ningún ADMIN, lo auto-asigna como ADMIN.
    Retorna (role_name, permissions).
    """
    result = await db.execute(
        select(UserRole, Role)
        .join(Role, UserRole.role_id == Role.id)
        .where(UserRole.user_email == email)
    )
    row = result.first()

    if row:
        _, role = row
        return role.name, role.permissions

    # Auto-asignar primer usuario como ADMIN
    admin_count_result = await db.execute(
        select(func.count())
        .select_from(UserRole)
        .join(Role, UserRole.role_id == Role.id)
        .where(Role.name == "ADMIN")
    )
    admin_count: int = admin_count_result.scalar_one()

    if admin_count == 0:
        admin_role_result = await db.execute(
            select(Role).where(Role.name == "ADMIN")
        )
        admin_role = admin_role_result.scalar_one()
        db.add(
            UserRole(
                user_email=email,
                role_id=admin_role.id,
                assigned_by="system_auto_first_user",
            )
        )
        await db.flush()
        log.info("first_user_auto_admin", email=email)
        return admin_role.name, admin_role.permissions

    # Usuario sin rol asignado: acceso denegado
    return None, {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/login", response_model=LoginUrlResponse, summary="Iniciar sesión con Microsoft")
async def login() -> LoginUrlResponse:
    """Retorna la URL de autorización de Azure AD para iniciar el flujo OAuth2."""
    state = secrets.token_urlsafe(32)
    auth_url = get_auth_url(state=state)
    return LoginUrlResponse(auth_url=auth_url, state=state)


@router.get("/callback", summary="Callback de Azure AD (navegador)")
async def callback(
    code: str = Query(..., description="Código de autorización de Azure AD"),
    state: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """
    Recibe el código de Azure AD, intercambia tokens y devuelve una página HTML
    que guarda los JWTs en localStorage y redirige al frontend.
    """
    try:
        token_result = exchange_code_for_token(code)
        user_info = extract_user_info(token_result)
    except ValueError as exc:
        error_html = f"""<!DOCTYPE html><html><body>
        <script>window.location.href='{settings.frontend_url}/login?error={exc}';</script>
        </body></html>"""
        return HTMLResponse(content=error_html, status_code=400)

    email = user_info["email"]
    name = user_info["name"]
    role_name, permissions = await _resolve_user_role(email, db)

    if role_name is None:
        error_html = f"""<!DOCTYPE html><html><body>
        <script>window.location.href='{settings.frontend_url}/login?error=sin_acceso';</script>
        </body></html>"""
        return HTMLResponse(content=error_html, status_code=403)

    access_token = create_access_token(email, name, role_name, permissions)
    refresh_token = create_refresh_token(email)
    expires_in = settings.jwt_expire_minutes * 60

    log.info("user_login_success", email=email, role=role_name)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Autenticando...</title></head>
<body>
<script>
try {{
    localStorage.setItem('cd_access_token', '{access_token}');
    localStorage.setItem('cd_refresh_token', '{refresh_token}');
    localStorage.setItem('cd_expires_in', '{expires_in}');
}} catch(e) {{ console.error('localStorage error', e); }}
window.location.replace('{settings.frontend_url}/');
</script>
<p style="font-family:sans-serif;text-align:center;margin-top:2rem">
  Autenticando, redirigiendo&hellip;
</p>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.post("/refresh", response_model=TokenResponse, summary="Renovar access token")
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Renueva el access token usando el refresh token.
    Consulta la BD para reflejar cambios de rol desde el último login.
    """
    payload = decode_token(body.refresh_token, expected_type="refresh")
    email: str = payload["sub"]

    # Re-consultar rol por si cambió desde el último login
    result = await db.execute(
        select(UserRole, Role)
        .join(Role, UserRole.role_id == Role.id)
        .where(UserRole.user_email == email)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sin rol asignado",
        )

    _, role = row
    name = email  # el nombre no está en el refresh token; se usa email como fallback

    return TokenResponse(
        access_token=create_access_token(email, name, role.name, role.permissions),
        refresh_token=create_refresh_token(email),
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.get("/me", response_model=UserInfoResponse, summary="Información del usuario actual")
async def me(current_user: CurrentUser = Depends(get_current_user)) -> UserInfoResponse:
    return UserInfoResponse(
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        permissions=current_user.permissions,
        is_admin=current_user.is_admin,
    )


@router.post("/logout", summary="Cerrar sesión")
async def logout() -> dict:
    """
    El cliente debe descartar sus tokens.
    El backend no mantiene lista de revocación (stateless).
    """
    return {"message": "Sesión cerrada correctamente"}
