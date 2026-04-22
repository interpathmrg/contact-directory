import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_admin
from app.database import get_db
from app.schemas.admin import (
    AssignRoleRequest,
    ChangeRoleRequest,
    RoleResponse,
    UserRoleResponse,
)
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Administración de Roles"])


def _svc(db: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(db)


# ---------------------------------------------------------------------------
# Roles disponibles
# ---------------------------------------------------------------------------

@router.get(
    "/roles",
    response_model=list[RoleResponse],
    summary="Listar roles disponibles",
)
async def list_roles(
    _user: CurrentUser = Depends(require_admin),
    svc: AdminService = Depends(_svc),
) -> list[RoleResponse]:
    roles = await svc.list_roles()
    return [RoleResponse.model_validate(r) for r in roles]


# ---------------------------------------------------------------------------
# Usuarios con acceso
# ---------------------------------------------------------------------------

@router.get(
    "/users",
    response_model=list[UserRoleResponse],
    summary="Listar usuarios con acceso y sus roles",
)
async def list_users(
    _user: CurrentUser = Depends(require_admin),
    svc: AdminService = Depends(_svc),
) -> list[UserRoleResponse]:
    users = await svc.list_users()
    return [UserRoleResponse.model_validate(u) for u in users]


@router.post(
    "/users",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar rol a un usuario",
)
async def assign_role(
    body: AssignRoleRequest,
    current_user: CurrentUser = Depends(require_admin),
    svc: AdminService = Depends(_svc),
) -> UserRoleResponse:
    """
    Da acceso a la aplicación a un usuario por su email de Azure AD.
    El usuario puede ser pre-registrado antes de su primer login.
    """
    user_role = await svc.assign_role(
        user_email=body.normalized_email,
        role_name=body.role_name,
        assigned_by=current_user.email,
    )
    return UserRoleResponse.model_validate(user_role)


@router.put(
    "/users/{user_role_id}/role",
    response_model=UserRoleResponse,
    summary="Cambiar el rol de un usuario",
)
async def change_role(
    user_role_id: uuid.UUID,
    body: ChangeRoleRequest,
    current_user: CurrentUser = Depends(require_admin),
    svc: AdminService = Depends(_svc),
) -> UserRoleResponse:
    """
    Cambia el rol de un usuario existente (ADMIN ↔ VIEWER).
    No permite dejar el sistema sin ningún ADMIN.
    """
    # Protección extra: un admin no puede cambiar su propio rol
    # (debe pedir a otro admin que lo haga)
    existing_users = await svc.list_users()
    target = next((u for u in existing_users if str(u.id) == str(user_role_id)), None)
    if target and target.user_email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes cambiar tu propio rol. Pide a otro administrador.",
        )

    user_role = await svc.change_role(
        user_role_id=user_role_id,
        role_name=body.role_name,
        changed_by=current_user.email,
    )
    return UserRoleResponse.model_validate(user_role)


@router.delete(
    "/users/{user_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revocar acceso de un usuario",
)
async def revoke_access(
    user_role_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_admin),
    svc: AdminService = Depends(_svc),
) -> None:
    """
    Elimina el acceso de un usuario a la aplicación.
    No permite eliminar al último ADMIN del sistema.
    No se puede revocar el propio acceso.
    """
    existing_users = await svc.list_users()
    target = next((u for u in existing_users if str(u.id) == str(user_role_id)), None)
    if target and target.user_email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes revocar tu propio acceso.",
        )

    await svc.revoke_access(
        user_role_id=user_role_id,
        revoked_by=current_user.email,
    )
