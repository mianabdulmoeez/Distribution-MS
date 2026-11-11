from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TenantCreate(BaseModel):
    business_name: str
    business_code: str
    city: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    owner_email: str | None = None
    timezone: str = "Asia/Karachi"


class TenantUpdate(BaseModel):
    business_name: str | None = None
    city: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    owner_email: str | None = None
    timezone: str | None = None
    status: str | None = None
    reason: str | None = None


class TenantResponse(BaseModel):
    id: UUID
    business_name: str
    business_code: str
    city: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    owner_email: str | None = None
    timezone: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TenantProvisionUser(BaseModel):
    full_name: str
    username: str
    password: str
    role: str = "business_admin"
    email: str | None = None
    phone: str | None = None
