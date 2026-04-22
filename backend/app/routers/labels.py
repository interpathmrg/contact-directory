from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_viewer
from app.database import get_db
from app.schemas.labels import LabelPreviewResponse, LabelRequest
from app.services.label_service import LabelService

router = APIRouter(prefix="/labels", tags=["Etiquetas de Invitación"])


def _svc(db: AsyncSession = Depends(get_db)) -> LabelService:
    return LabelService(db)


# ---------------------------------------------------------------------------
# Preview  (ADMIN + VIEWER)
# ---------------------------------------------------------------------------

@router.post(
    "/preview",
    response_model=LabelPreviewResponse,
    summary="Vista previa de contactos para etiquetas",
)
async def labels_preview(
    req: LabelRequest,
    _user: CurrentUser = Depends(require_viewer),
    svc: LabelService = Depends(_svc),
) -> LabelPreviewResponse:
    """
    Retorna la lista de contactos que serán incluidos en las etiquetas,
    con el ordenamiento seleccionado. Sin generar PDF.
    """
    return await svc.build_preview(req)


# ---------------------------------------------------------------------------
# Generación PDF  (ADMIN + VIEWER)
# ---------------------------------------------------------------------------

@router.post(
    "/pdf",
    summary="Generar PDF de etiquetas de invitación (Avery 5163)",
    response_class=Response,
)
async def labels_pdf(
    req: LabelRequest,
    _user: CurrentUser = Depends(require_viewer),
    svc: LabelService = Depends(_svc),
) -> Response:
    """
    Genera un PDF con etiquetas de invitación en formato Avery 5163
    (2 columnas × 5 filas = 10 por página).

    Cada etiqueta contiene:
      - Nombre Apellido  (negrita)
      - Empresa
      - Sociedad  (cursiva, gris)
    """
    pdf_bytes = await svc.generate_pdf(req)

    if not pdf_bytes:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="No se encontraron contactos con los filtros indicados",
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=etiquetas_invitacion.pdf"
        },
    )
