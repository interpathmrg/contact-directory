from pydantic import BaseModel


class ImportRowInput(BaseModel):
    """Datos de una fila parseada del archivo de importación."""
    nombre: str = ""
    apellido: str = ""
    empresa: str = ""
    cargo: str = ""
    puesto: str = ""
    direccion: str = ""
    telefono: str = ""
    celular: str = ""
    email: str = ""
    nombre_contacto_interno: str = ""
    email_contacto_interno: str = ""
    telefono_contacto_interno: str = ""
    nota: str = ""
    sociedad: str = ""  # Nombre de la sociedad (se resuelve a ID en el servicio)


class ImportRowPreview(BaseModel):
    row_number: int
    data: ImportRowInput
    errors: list[str]
    is_valid: bool


class ImportPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[ImportRowPreview]


class ImportConfirmRequest(BaseModel):
    """El cliente envía las filas válidas que quiere importar."""
    rows: list[ImportRowInput]


class ImportResultRow(BaseModel):
    row_number: int
    email: str
    nombre: str
    apellido: str
    status: str  # "created" | "skipped" | "error"
    message: str = ""


class ImportConfirmResponse(BaseModel):
    total: int
    created: int
    skipped: int
    errors: int
    results: list[ImportResultRow]


class ExportPreviewResponse(BaseModel):
    total_contacts: int
    sample_rows: list[dict]
    filters_applied: dict
