from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    full_name: str
    username: str
    password: str
    phone: str | None = None
    email: str | None = None
    role: str = "salesperson"


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: str | None = None
    phone: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipResponse(BaseModel):
    id: UUID
    user_id: UUID
    tenant_id: UUID
    username: str
    role: str
    status: str
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResetPasswordRequest(BaseModel):
    new_password: str
    must_change: bool = True
