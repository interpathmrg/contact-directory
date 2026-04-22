from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.contact import Contact


class Society(Base):
    """Sociedad empresarial a la que pertenece un contacto."""

    __tablename__ = "societies"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    contacts: Mapped[list[Contact]] = relationship(back_populates="society")

    def __repr__(self) -> str:
        return f"<Society id={self.id} name={self.name!r}>"
