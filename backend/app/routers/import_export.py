from __future__ import annotations

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import CurrentUser, require_admin
from app.config import get_settings
from app.database import get_db
from app.models.contact import Contact
from app.models.society import Society
from app.schemas.import_export import (
    ExportPreviewResponse,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportPreviewResponse,
)
from app.services.import_service import ImportService
from app.utils.excel_handler import (
    contacts_to_csv,
    contacts_to_excel,
    generate_template,
    parse_csv,
    parse_excel,
)

log = structlog.get_logger()
settings = get_settings()
router = APIRouter(tags=["Importación / Exportación"])

_ALLOWED_EXTENSIONS = {".xlsx", ".csv"}
_MAX_BYTES = settings.upload_max_size_mb * 1024 * 1024


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _fetch_societies(db: AsyncSession) -> list[Society]:
    result = await db.execute(select(Society).order_by(Society.name))
    return list(result.scalars().all())


async def _fetch_contacts_for_export(
    db: AsyncSession,
    sociedad_id: int | None,
    empresa: str | None,
    is_active: bool,
) -> list[dict]:
    q = (
        select(Contact)
        .options(selectinload(Contact.society))
        .where(Contact.is_active == is_active)
    )
    if sociedad_id:
        q = q.where(Contact.sociedad_id == sociedad_id)
    if empresa:
        q = q.where(Contact.empresa.ilike(f"%{empresa}%"))

    q = q.order_by(Contact.apellido, Contact.nombre)
    result = await db.execute(q)
    contacts = result.scalars().all()

    rows: list[dict] = []
    for c in contacts:
        rows.append({
            "nombre": c.nombre,
            "apellido": c.apellido,
            "empresa": c.empresa or "",
            "cargo": c.cargo or "",
            "puesto": c.puesto or "",
            "direccion": c.direccion or "",
            "telefono": c.telefono or "",
            "celular": c.celular or "",
            "email": c.email or "",
            "nombre_contacto_interno": c.nombre_contacto_interno or "",
            "email_contacto_interno": c.email_contacto_interno or "",
            "telefono_contacto_interno": c.telefono_contacto_interno or "",
            "nota": c.nota or "",
            "sociedad": c.society.name if c.society else "",
        })
    return rows


# ---------------------------------------------------------------------------
# IMPORTACIÓN
# ---------------------------------------------------------------------------

@router.get(
    "/import/template",
    summary="Descargar plantilla Excel para importación",
    response_class=Response,
)
async def download_template(
    _user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    societies = await _fetch_societies(db)
    society_names = [s.name for s in societies]
    content = generate_template(society_names=society_names)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_contactos.xlsx"},
    )


@router.post(
    "/import/preview",
    response_model=ImportPreviewResponse,
    summary="Preview de importación (sin guardar datos)",
)
async def import_preview(
    file: UploadFile,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ImportPreviewResponse:
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tipo de archivo no soportado '{ext}'. Use .xlsx o .csv",
        )

    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo demasiado grande (máximo {settings.upload_max_size_mb} MB)",
        )

    try:
        raw_rows = parse_excel(content) if ext == ".xlsx" else parse_csv(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error al parsear el archivo: {exc}",
        )

    if not raw_rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo no contiene datos (o solo tiene el encabezado)",
        )

    svc = ImportService(db)
    preview = await svc.build_preview(raw_rows, filename=filename)
    log.info(
        "import_preview",
        filename=filename,
        total=preview.total_rows,
        valid=preview.valid_rows,
        by=current_user.email,
    )
    return preview


@router.post(
    "/import/confirm",
    response_model=ImportConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirmar importación de las filas válidas",
)
async def import_confirm(
    body: ImportConfirmRequest,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ImportConfirmResponse:
    if not body.rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No hay filas para importar",
        )

    svc = ImportService(db)
    return await svc.confirm_import(body.rows, user_email=current_user.email)


# ---------------------------------------------------------------------------
# EXPORTACIÓN
# ---------------------------------------------------------------------------

@router.get(
    "/export/preview",
    response_model=ExportPreviewResponse,
    summary="Preview de exportación (resumen y muestra)",
)
async def export_preview(
    sociedad_id: int | None = Query(None),
    empresa: str | None = Query(None),
    is_active: bool = Query(True),
    _user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ExportPreviewResponse:
    rows = await _fetch_contacts_for_export(db, sociedad_id, empresa, is_active)
    filters: dict = {}
    if sociedad_id:
        filters["sociedad_id"] = sociedad_id
    if empresa:
        filters["empresa"] = empresa
    filters["is_active"] = is_active

    return ExportPreviewResponse(
        total_contacts=len(rows),
        sample_rows=rows[:5],
        filters_applied=filters,
    )


@router.get(
    "/export/download",
    summary="Descargar contactos como Excel o CSV",
    response_class=Response,
)
async def export_download(
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    sociedad_id: int | None = Query(None),
    empresa: str | None = Query(None),
    is_active: bool = Query(True),
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    rows = await _fetch_contacts_for_export(db, sociedad_id, empresa, is_active)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if format == "xlsx":
        content = contacts_to_excel(rows)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"contactos_{timestamp}.xlsx"
    else:
        content = contacts_to_csv(rows)
        media_type = "text/csv; charset=utf-8"
        filename = f"contactos_{timestamp}.csv"

    log.info("export_download", format=format, rows=len(rows), by=current_user.email)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
