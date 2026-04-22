from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.society import Society


class Contact(Base):
    """Contacto corporativo con información de empresa y enlace interno."""

    __tablename__ = "contacts"
    __table_args__ = (
        # Índice compuesto para búsqueda por nombre
        Index("ix_contacts_nombre_apellido", "nombre", "apellido"),
        # Índice para filtrar activos por sociedad
        Index("ix_contacts_sociedad_active", "sociedad_id", "is_active"),
        # Índice para búsqueda por empresa
        Index("ix_contacts_empresa", "empresa"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    empresa: Mapped[str | None] = mapped_column(String(200))
    cargo: Mapped[str | None] = mapped_column(String(100))
    puesto: Mapped[str | None] = mapped_column(String(200))
    direccion: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(String(20))
    celular: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(
        String(150), unique=True, index=True, nullable=True
    )
    nombre_contacto_interno: Mapped[str | None] = mapped_column(String(200))
    email_contacto_interno: Mapped[str | None] = mapped_column(String(150))
    telefono_contacto_interno: Mapped[str | None] = mapped_column(String(20))
    nota: Mapped[str | None] = mapped_column(Text)

    sociedad_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("societies.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    updated_by: Mapped[str | None] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    society: Mapped[Society | None] = relationship(back_populates="contacts")

    def __repr__(self) -> str:
        return f"<Contact {self.nombre} {self.apellido} ({self.email})>"
