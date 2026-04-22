import math
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.society import SocietyResponse


class ContactBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    empresa: str | None = Field(None, max_length=200)
    cargo: str | None = Field(None, max_length=100)
    puesto: str | None = Field(None, max_length=200)
    direccion: str | None = None
    telefono: str | None = Field(None, max_length=20)
    celular: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=150)
    nombre_contacto_interno: str | None = Field(None, max_length=200)
    email_contacto_interno: str | None = Field(None, max_length=150)
    telefono_contacto_interno: str | None = Field(None, max_length=20)
    nota: str | None = None
    sociedad_id: int | None = None

    @field_validator("email", "email_contacto_interno", mode="before")
    @classmethod
    def normalise_email(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip().lower()
            return v if v else None
        return None

    @field_validator("nombre", "apellido", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip()


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    """Todos los campos opcionales: el cliente envía el formulario completo."""
    nombre: str | None = Field(None, min_length=1, max_length=100)
    apellido: str | None = Field(None, min_length=1, max_length=100)
    empresa: str | None = Field(None, max_length=200)
    cargo: str | None = Field(None, max_length=100)
    puesto: str | None = Field(None, max_length=200)
    direccion: str | None = None
    telefono: str | None = Field(None, max_length=20)
    celular: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=150)
    nombre_contacto_interno: str | None = Field(None, max_length=200)
    email_contacto_interno: str | None = Field(None, max_length=150)
    telefono_contacto_interno: str | None = Field(None, max_length=20)
    nota: str | None = None
    sociedad_id: int | None = None

    @field_validator("email", "email_contacto_interno", mode="before")
    @classmethod
    def normalise_email(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip().lower()
            return v if v else None
        return None


class ContactResponse(ContactBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    updated_by: str | None = None
    is_active: bool
    society: SocietyResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedContactsResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(
        cls,
        items: list[ContactResponse],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedContactsResponse":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )
