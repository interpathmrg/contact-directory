from __future__ import annotations

import uuid

import structlog
from sqlalchemy import asc, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.society import Society
from app.schemas.labels import LabelContactItem, LabelPreviewResponse, LabelRequest
from app.utils.pdf_generator import LabelData, generate_labels_pdf

log = structlog.get_logger()

# Columnas válidas para ordenamiento
_ORDER_MAP = {
    "apellido": [Contact.apellido, Contact.nombre],
    "nombre":   [Contact.nombre, Contact.apellido],
    "empresa":  [Contact.empresa, Contact.apellido],
    "sociedad": [Contact.sociedad_id, Contact.apellido],  # join resuelve el nombre
}


class LabelService:
    """Lógica de negocio para selección y generación de etiquetas de invitación."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_contacts(self, req: LabelRequest) -> list[Contact]:
        """Retorna contactos activos según los filtros / IDs del request."""
        q = (
            select(Contact)
            .options(selectinload(Contact.society))
            .where(Contact.is_active == True)  # noqa: E712
        )

        if req.contact_ids:
            # Selección explícita por IDs — ignora los demás filtros
            q = q.where(Contact.id.in_(req.contact_ids))
        else:
            if req.sociedad_ids:
                q = q.where(Contact.sociedad_id.in_(req.sociedad_ids))
            if req.empresa:
                q = q.where(Contact.empresa.ilike(f"%{req.empresa}%"))
            if req.nombre:
                pattern = f"%{req.nombre}%"
                q = q.where(
                    Contact.nombre.ilike(pattern) | Contact.apellido.ilike(pattern)
                )

        order_cols = _ORDER_MAP.get(req.order_by, _ORDER_MAP["apellido"])
        for col in order_cols:
            q = q.order_by(asc(col))

        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def build_preview(self, req: LabelRequest) -> LabelPreviewResponse:
        contacts = await self.get_contacts(req)
        items = [
            LabelContactItem(
                id=c.id,
                nombre=c.nombre,
                apellido=c.apellido,
                empresa=c.empresa,
                sociedad=c.society.name if c.society else None,
            )
            for c in contacts
        ]
        return LabelPreviewResponse(total=len(items), contacts=items)

    async def generate_pdf(self, req: LabelRequest) -> bytes:
        contacts = await self.get_contacts(req)

        labels = [
            LabelData(
                nombre_completo=f"{c.nombre} {c.apellido}".strip(),
                empresa=c.empresa or "",
                sociedad=c.society.name if c.society else "",
            )
            for c in contacts
        ]

        log.info(
            "labels_pdf_generated",
            total=len(labels),
            order_by=req.order_by,
        )
        return generate_labels_pdf(labels)
