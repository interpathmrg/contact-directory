from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import structlog
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contact import Contact
from app.models.society import Society
from app.schemas.contact import ContactCreate, ContactUpdate

log = structlog.get_logger()

# Columnas permitidas para ordenamiento (previene SQL injection)
_SORTABLE: dict[str, Any] = {
    "nombre": Contact.nombre,
    "apellido": Contact.apellido,
    "empresa": Contact.empresa,
    "email": Contact.email,
    "cargo": Contact.cargo,
    "sociedad_id": Contact.sociedad_id,
    "created_at": Contact.created_at,
    "updated_at": Contact.updated_at,
}


@dataclass
class PaginatedResult:
    items: list[Contact]
    total: int


class ContactService:
    """Lógica de negocio para el directorio de contactos."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    async def list_contacts(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "apellido",
        order_dir: str = "asc",
        search: str | None = None,
        sociedad_id: int | None = None,
        empresa: str | None = None,
        nombre: str | None = None,
        email: str | None = None,
        is_active: bool = True,
    ) -> PaginatedResult:
        base_q = (
            select(Contact)
            .options(selectinload(Contact.society))
            .where(Contact.is_active == is_active)
        )

        # Filtros simples
        if sociedad_id is not None:
            base_q = base_q.where(Contact.sociedad_id == sociedad_id)
        if empresa:
            base_q = base_q.where(
                Contact.empresa.ilike(f"%{empresa}%")
            )
        if nombre:
            pattern = f"%{nombre}%"
            base_q = base_q.where(
                Contact.nombre.ilike(pattern) | Contact.apellido.ilike(pattern)
            )
        if email:
            base_q = base_q.where(Contact.email.ilike(f"%{email}%"))

        # Búsqueda full-text con GIN index
        if search:
            search_vector = func.to_tsvector(
                "spanish",
                func.concat(
                    func.coalesce(Contact.nombre, ""),
                    " ",
                    func.coalesce(Contact.apellido, ""),
                    " ",
                    func.coalesce(Contact.empresa, ""),
                    " ",
                    func.coalesce(Contact.email, ""),
                ),
            )
            tsquery = func.plainto_tsquery("spanish", search)
            base_q = base_q.where(search_vector.op("@@")(tsquery))

        # Total (sin paginación)
        count_q = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._db.execute(count_q)).scalar_one()

        # Ordenamiento
        col = _SORTABLE.get(order_by, Contact.apellido)
        order_fn = asc if order_dir.lower() != "desc" else desc
        base_q = base_q.order_by(order_fn(col))

        # Paginación
        offset = (page - 1) * page_size
        base_q = base_q.offset(offset).limit(page_size)

        result = await self._db.execute(base_q)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total)

    async def get_by_id(self, contact_id: uuid.UUID) -> Contact | None:
        result = await self._db.execute(
            select(Contact)
            .options(selectinload(Contact.society))
            .where(Contact.id == contact_id, Contact.is_active == True)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def list_societies(self) -> list[Society]:
        result = await self._db.execute(select(Society).order_by(Society.name))
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    async def create(self, data: ContactCreate, user_email: str) -> Contact:
        await self._assert_society_exists(data.sociedad_id)
        await self._assert_email_unique(data.email)

        contact = Contact(**data.model_dump(), updated_by=user_email)
        self._db.add(contact)
        await self._db.flush()
        await self._db.refresh(contact, ["society"])
        log.info("contact_created", id=str(contact.id), by=user_email)
        return contact

    async def update(
        self, contact_id: uuid.UUID, data: ContactUpdate, user_email: str
    ) -> Contact:
        contact = await self._get_or_404(contact_id)

        updates = data.model_dump(exclude_none=True)
        if not updates:
            return contact

        if "sociedad_id" in updates:
            await self._assert_society_exists(updates["sociedad_id"])

        if "email" in updates and updates["email"] != contact.email:
            await self._assert_email_unique(updates["email"], exclude_id=contact_id)

        for field, value in updates.items():
            setattr(contact, field, value)
        contact.updated_by = user_email

        await self._db.flush()
        await self._db.refresh(contact, ["society"])
        log.info("contact_updated", id=str(contact_id), by=user_email)
        return contact

    async def soft_delete(self, contact_id: uuid.UUID, user_email: str) -> Contact:
        contact = await self._get_or_404(contact_id)
        contact.is_active = False
        contact.updated_by = user_email
        await self._db.flush()
        log.info("contact_deleted", id=str(contact_id), by=user_email)
        return contact

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _get_or_404(self, contact_id: uuid.UUID) -> Contact:
        contact = await self.get_by_id(contact_id)
        if not contact:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        return contact

    async def _assert_society_exists(self, sociedad_id: int | None) -> None:
        if sociedad_id is None:
            return
        result = await self._db.execute(
            select(Society).where(Society.id == sociedad_id)
        )
        if not result.scalar_one_or_none():
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422, detail=f"La sociedad con id={sociedad_id} no existe"
            )

    async def _assert_email_unique(
        self,
        email: str | None,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        if not email:
            return
        q = select(Contact).where(
            Contact.email == email, Contact.is_active == True  # noqa: E712
        )
        if exclude_id:
            q = q.where(Contact.id != exclude_id)
        existing = (await self._db.execute(q)).scalar_one_or_none()
        if existing:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un contacto activo con el email '{email}'",
            )
