import uuid
from pydantic import BaseModel, Field


class LabelContactItem(BaseModel):
    id: uuid.UUID
    nombre: str
    apellido: str
    empresa: str | None = None
    sociedad: str | None = None


class LabelPreviewResponse(BaseModel):
    total: int
    contacts: list[LabelContactItem]


class LabelRequest(BaseModel):
    """Filtros para generar o previsualizar etiquetas."""
    sociedad_ids: list[int] | None = Field(
        None, description="IDs de sociedades (multiselect)"
    )
    empresa: str | None = Field(None, description="Filtro parcial por empresa")
    nombre: str | None = Field(None, description="Filtro parcial por nombre o apellido")
    contact_ids: list[uuid.UUID] | None = Field(
        None, description="IDs explícitos de contactos (tiene precedencia sobre filtros)"
    )
    order_by: str = Field(
        "apellido",
        description="Ordenamiento: apellido | nombre | empresa | sociedad",
    )
