from pydantic import BaseModel, EmailStr, Field


class LoginUrlResponse(BaseModel):
    auth_url: str
    state: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Segundos hasta expiración")
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UserInfoResponse(BaseModel):
    email: str
    name: str
    role: str | None = None
    permissions: dict = {}
    is_admin: bool = False
