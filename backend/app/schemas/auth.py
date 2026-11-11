from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    business_code: str
    username: str
    password: str
    device_info: str | None = None


class PlatformLoginRequest(BaseModel):
    username: str
    password: str
    device_info: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID
    full_name: str
    role: str | None = None
    tenant_id: UUID | None = None
    business_name: str | None = None
    membership_id: UUID | None = None
    must_change_password: bool = False
    is_platform_admin: bool = False
