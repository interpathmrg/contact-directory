import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user, require_admin
from app.database import get_db
from app.schemas.contact import (
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    PaginatedContactsResponse,
)
from app.schemas.society import SocietyResponse
from app.services.contact_service import ContactService

router = APIRouter(prefix="/contacts", tags=["Contactos"])


def _svc(db: AsyncSession = Depends(get_db)) -> ContactService:
    return ContactService(db)


# ---------------------------------------------------------------------------
# Endpoints de lectura  (VIEWER + ADMIN)
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=PaginatedContactsResponse,
    summary="Listar contactos con paginación y filtros",
)
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("apellido"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
    search: str | None = Query(None, description="Búsqueda full-text"),
    sociedad_id: int | None = Query(None),
    empresa: str | None = Query(None),
    nombre: str | None = Query(None),
    email: str | None = Query(None),
    is_active: bool = Query(True),
    _user: CurrentUser = Depends(get_current_user),
    svc: ContactService = Depends(_svc),
) -> PaginatedContactsResponse:
    result = await svc.list_contacts(
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir,
        search=search,
        sociedad_id=sociedad_id,
        empresa=empresa,
        nombre=nombre,
        email=email,
        is_active=is_active,
    )
    return PaginatedContactsResponse.build(
        items=[ContactResponse.model_validate(c) for c in result.items],
        total=result.total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Obtener un contacto por ID",
)
async def get_contact(
    contact_id: uuid.UUID,
    _user: CurrentUser = Depends(get_current_user),
    svc: ContactService = Depends(_svc),
) -> ContactResponse:
    contact = await svc.get_by_id(contact_id)
    if not contact:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return ContactResponse.model_validate(contact)


# ---------------------------------------------------------------------------
# Endpoints de escritura  (solo ADMIN)
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un contacto",
)
async def create_contact(
    data: ContactCreate,
    current_user: CurrentUser = Depends(require_admin),
    svc: ContactService = Depends(_svc),
) -> ContactResponse:
    contact = await svc.create(data, user_email=current_user.email)
    return ContactResponse.model_validate(contact)


@router.put(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Actualizar un contacto",
)
async def update_contact(
    contact_id: uuid.UUID,
    data: ContactUpdate,
    current_user: CurrentUser = Depends(require_admin),
    svc: ContactService = Depends(_svc),
) -> ContactResponse:
    contact = await svc.update(contact_id, data, user_email=current_user.email)
    return ContactResponse.model_validate(contact)


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un contacto (soft delete)",
)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_admin),
    svc: ContactService = Depends(_svc),
) -> None:
    await svc.soft_delete(contact_id, user_email=current_user.email)


# ---------------------------------------------------------------------------
# Sociedades  (lookup para dropdowns)
# ---------------------------------------------------------------------------

@router.get(
    "/societies/all",
    response_model=list[SocietyResponse],
    tags=["Sociedades"],
    summary="Listar todas las sociedades",
)
async def list_societies(
    _user: CurrentUser = Depends(get_current_user),
    svc: ContactService = Depends(_svc),
) -> list[SocietyResponse]:
    societies = await svc.list_societies()
    return [SocietyResponse.model_validate(s) for s in societies]
