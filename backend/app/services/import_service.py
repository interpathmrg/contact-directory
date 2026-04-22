from __future__ import annotations

import re
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.society import Society
from app.schemas.import_export import (
    ImportConfirmResponse,
    ImportPreviewResponse,
    ImportResultRow,
    ImportRowInput,
    ImportRowPreview,
)
from app.utils.excel_handler import COLUMNS

log = structlog.get_logger()

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class ImportService:
    """Lógica de negocio para importación y exportación masiva."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._society_map: dict[str, int] = {}  # nombre.lower() → id

    async def _load_societies(self) -> None:
        if self._society_map:
            return
        result = await self._db.execute(select(Society))
        for s in result.scalars().all():
            self._society_map[s.name.lower()] = s.id

    async def build_preview(
        self,
        raw_rows: list[dict[str, str]],
        filename: str,
    ) -> ImportPreviewResponse:
        """Valida todas las filas y retorna el preview con errores anotados."""
        await self._load_societies()

        # Detectar emails duplicados dentro del mismo archivo
        seen_emails: set[str] = set()

        preview_rows: list[ImportRowPreview] = []
        for idx, raw in enumerate(raw_rows, start=2):  # row 1 = header
            row_input = ImportRowInput(**{f: raw.get(f, "") for f, _, _ in COLUMNS})
            errors = self._validate_row(row_input, seen_emails)
            if row_input.email:
                seen_emails.add(row_input.email.lower())
            preview_rows.append(
                ImportRowPreview(
                    row_number=idx,
                    data=row_input,
                    errors=errors,
                    is_valid=len(errors) == 0,
                )
            )

        valid = sum(1 for r in preview_rows if r.is_valid)
        return ImportPreviewResponse(
            filename=filename,
            total_rows=len(preview_rows),
            valid_rows=valid,
            invalid_rows=len(preview_rows) - valid,
            rows=preview_rows,
        )

    async def confirm_import(
        self,
        rows: list[ImportRowInput],
        user_email: str,
    ) -> ImportConfirmResponse:
        """Importa las filas válidas. Omite emails ya existentes en BD."""
        await self._load_societies()

        results: list[ImportResultRow] = []
        created = skipped = errors = 0

        # Cargar emails existentes en BD de una sola consulta
        existing_emails = await self._fetch_existing_emails(
            {r.email.lower() for r in rows if r.email}
        )

        for idx, row in enumerate(rows, start=1):
            email_key = row.email.lower() if row.email else ""

            if email_key and email_key in existing_emails:
                results.append(ImportResultRow(
                    row_number=idx,
                    email=row.email,
                    nombre=row.nombre,
                    apellido=row.apellido,
                    status="skipped",
                    message="Email ya existe en el sistema",
                ))
                skipped += 1
                continue

            try:
                contact = self._row_to_contact(row, user_email)
                self._db.add(contact)
                if email_key:
                    existing_emails.add(email_key)
                results.append(ImportResultRow(
                    row_number=idx,
                    email=row.email,
                    nombre=row.nombre,
                    apellido=row.apellido,
                    status="created",
                ))
                created += 1
            except Exception as exc:
                log.warning("import_row_failed", row=idx, error=str(exc))
                results.append(ImportResultRow(
                    row_number=idx,
                    email=row.email,
                    nombre=row.nombre,
                    apellido=row.apellido,
                    status="error",
                    message=str(exc),
                ))
                errors += 1

        await self._db.flush()
        log.info(
            "import_completed",
            created=created,
            skipped=skipped,
            errors=errors,
            by=user_email,
        )
        return ImportConfirmResponse(
            total=len(rows),
            created=created,
            skipped=skipped,
            errors=errors,
            results=results,
        )

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _validate_row(
        self,
        row: ImportRowInput,
        seen_emails: set[str],
    ) -> list[str]:
        errs: list[str] = []

        if not row.nombre.strip():
            errs.append("Nombre es obligatorio")
        if not row.apellido.strip():
            errs.append("Apellido es obligatorio")

        if row.email:
            email_lower = row.email.lower()
            if not _EMAIL_RE.match(email_lower):
                errs.append(f"Email '{row.email}' no es válido")
            elif email_lower in seen_emails:
                errs.append(f"Email '{row.email}' duplicado en el archivo")

        if row.email_contacto_interno and not _EMAIL_RE.match(
            row.email_contacto_interno.lower()
        ):
            errs.append(f"Email contacto interno '{row.email_contacto_interno}' no es válido")

        if row.sociedad and row.sociedad.lower() not in self._society_map:
            validos = ", ".join(k.title() for k in self._society_map)
            errs.append(
                f"Sociedad '{row.sociedad}' no existe. Valores válidos: {validos}"
            )

        return errs

    def _row_to_contact(self, row: ImportRowInput, user_email: str) -> Contact:
        sociedad_id: int | None = None
        if row.sociedad:
            sociedad_id = self._society_map.get(row.sociedad.lower())

        return Contact(
            nombre=row.nombre.strip(),
            apellido=row.apellido.strip(),
            empresa=row.empresa.strip() or None,
            cargo=row.cargo.strip() or None,
            puesto=row.puesto.strip() or None,
            direccion=row.direccion.strip() or None,
            telefono=row.telefono.strip() or None,
            celular=row.celular.strip() or None,
            email=row.email.lower().strip() or None,
            nombre_contacto_interno=row.nombre_contacto_interno.strip() or None,
            email_contacto_interno=row.email_contacto_interno.lower().strip() or None,
            telefono_contacto_interno=row.telefono_contacto_interno.strip() or None,
            nota=row.nota.strip() or None,
            sociedad_id=sociedad_id,
            updated_by=user_email,
        )

    async def _fetch_existing_emails(self, emails: set[str]) -> set[str]:
        if not emails:
            return set()
        result = await self._db.execute(
            select(Contact.email).where(
                Contact.email.in_(list(emails)),
                Contact.is_active == True,  # noqa: E712
            )
        )
        return {row[0].lower() for row in result.all() if row[0]}
