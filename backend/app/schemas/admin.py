import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    permissions: dict = {}

    model_config = ConfigDict(from_attributes=True)


class UserRoleResponse(BaseModel):
    id: uuid.UUID
    user_email: str
    role: RoleResponse
    assigned_by: str | None = None
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignRoleRequest(BaseModel):
    user_email: str = Field(..., description="Email del usuario a dar acceso")
    role_name: str = Field(..., description="Nombre del rol: ADMIN | VIEWER")

    @property
    def normalized_email(self) -> str:
        return self.user_email.strip().lower()


class ChangeRoleRequest(BaseModel):
    role_name: str = Field(..., description="Nuevo rol: ADMIN | VIEWER")
