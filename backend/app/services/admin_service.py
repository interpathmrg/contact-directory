from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.user_role import UserRole

log = structlog.get_logger()


class AdminService:
    """Gestión de acceso de usuarios (asignación y revocación de roles)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    async def list_users(self) -> list[UserRole]:
        result = await self._db.execute(
            select(UserRole)
            .options(selectinload(UserRole.role))
            .order_by(UserRole.assigned_at)
        )
        return list(result.scalars().all())

    async def list_roles(self) -> list[Role]:
        result = await self._db.execute(select(Role).order_by(Role.id))
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Mutaciones
    # ------------------------------------------------------------------

    async def assign_role(
        self,
        user_email: str,
        role_name: str,
        assigned_by: str,
    ) -> UserRole:
        """
        Asigna un rol a un usuario por email.
        Si ya tiene rol asignado lanza 409. Si el rol no existe lanza 422.
        """
        email = user_email.strip().lower()
        role = await self._get_role_or_422(role_name)

        # Verificar si ya existe
        existing = await self._db.execute(
            select(UserRole).where(UserRole.user_email == email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El usuario '{email}' ya tiene un rol asignado. "
                       "Use el endpoint de cambio de rol.",
            )

        user_role = UserRole(
            user_email=email,
            role_id=role.id,
            assigned_by=assigned_by,
        )
        self._db.add(user_role)
        await self._db.flush()
        await self._db.refresh(user_role, ["role"])

        log.info("role_assigned", email=email, role=role_name, by=assigned_by)
        return user_role

    async def change_role(
        self,
        user_role_id: uuid.UUID,
        role_name: str,
        changed_by: str,
    ) -> UserRole:
        """
        Cambia el rol de un usuario existente.
        Impide dejar el sistema sin ningún ADMIN.
        """
        user_role = await self._get_user_role_or_404(user_role_id)
        new_role = await self._get_role_or_422(role_name)

        # Si baja de ADMIN, verificar que no sea el último
        if user_role.role.name == "ADMIN" and new_role.name != "ADMIN":
            await self._assert_not_last_admin(exclude_id=user_role_id)

        user_role.role_id = new_role.id
        await self._db.flush()
        await self._db.refresh(user_role, ["role"])

        log.info(
            "role_changed",
            email=user_role.user_email,
            new_role=role_name,
            by=changed_by,
        )
        return user_role

    async def revoke_access(
        self,
        user_role_id: uuid.UUID,
        revoked_by: str,
    ) -> None:
        """
        Elimina el acceso de un usuario.
        Impide eliminar al último ADMIN del sistema.
        """
        user_role = await self._get_user_role_or_404(user_role_id)

        if user_role.role.name == "ADMIN":
            await self._assert_not_last_admin(exclude_id=user_role_id)

        email = user_role.user_email
        await self._db.delete(user_role)
        await self._db.flush()

        log.info("access_revoked", email=email, by=revoked_by)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _get_role_or_422(self, role_name: str) -> Role:
        result = await self._db.execute(
            select(Role).where(Role.name == role_name.upper())
        )
        role = result.scalar_one_or_none()
        if not role:
            result_all = await self._db.execute(select(Role.name))
            valid = [r[0] for r in result_all.all()]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Rol '{role_name}' no existe. Roles válidos: {valid}",
            )
        return role

    async def _get_user_role_or_404(self, user_role_id: uuid.UUID) -> UserRole:
        result = await self._db.execute(
            select(UserRole)
            .options(selectinload(UserRole.role))
            .where(UserRole.id == user_role_id)
        )
        user_role = result.scalar_one_or_none()
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        return user_role

    async def _assert_not_last_admin(
        self, exclude_id: uuid.UUID | None = None
    ) -> None:
        """Lanza 422 si la operación dejaría el sistema sin ningún ADMIN."""
        q = (
            select(func.count())
            .select_from(UserRole)
            .join(Role, UserRole.role_id == Role.id)
            .where(Role.name == "ADMIN")
        )
        if exclude_id:
            q = q.where(UserRole.id != exclude_id)

        count: int = (await self._db.execute(q)).scalar_one()
        if count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede realizar esta operación: quedaría el sistema sin ningún administrador.",
            )
