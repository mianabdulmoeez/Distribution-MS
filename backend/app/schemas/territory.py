from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


# --- Area ---
class AreaCreate(BaseModel):
    name: str
    description: str | None = None


class AreaUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class AreaResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Area Assignment ---
class AreaAssignmentCreate(BaseModel):
    membership_id: UUID
    start_date: date | None = None
    end_date: date | None = None


class AreaAssignmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    area_id: UUID
    membership_id: UUID
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Shop ---
class ShopCreate(BaseModel):
    name: str
    area_id: UUID
    contact_person: str | None = None
    contact_phone: str | None = None
    address: str
    landmark: str | None = None
    city: str
    entrance_lat: float
    entrance_lng: float
    entrance_pin: str
    photo_url: str | None = None
    radius_meters: float = 10.0


class ShopUpdate(BaseModel):
    name: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    landmark: str | None = None
    city: str | None = None
    entrance_lat: float | None = None
    entrance_lng: float | None = None
    entrance_pin: str | None = None
    radius_meters: float | None = None
    area_id: UUID | None = None
    reason: str | None = None


class ShopResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    area_id: UUID
    name: str
    contact_person: str | None = None
    contact_phone: str | None = None
    address: str
    landmark: str | None = None
    city: str
    entrance_lat: float
    entrance_lng: float
    entrance_pin: str
    status: str
    photo_url: str | None = None
    radius_meters: float
    pin_version: int
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShopApproveRequest(BaseModel):
    entrance_lat: float | None = None
    entrance_lng: float | None = None


class ShopRejectRequest(BaseModel):
    reason: str


# --- Shop Proposal ---
class ShopProposalCreate(BaseModel):
    name: str
    contact_person: str | None = None
    contact_phone: str | None = None
    address: str
    landmark: str | None = None
    city: str
    area_id: UUID
    lat: float
    lng: float
    accuracy_meters: float | None = None
    entrance_pin: str
    photo_url: str | None = None


class ShopProposalResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    shop_id: UUID | None = None
    proposed_by: UUID
    name: str
    contact_person: str | None = None
    contact_phone: str | None = None
    address: str
    landmark: str | None = None
    city: str
    area_id: UUID
    lat: float
    lng: float
    accuracy_meters: float | None = None
    entrance_pin: str
    photo_url: str | None = None
    status: str
    rejection_reason: str | None = None
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Planned Stop ---
class PlannedStopCreate(BaseModel):
    membership_id: UUID
    service_date: date
    stops: list["StopItem"]


class StopItem(BaseModel):
    shop_id: UUID
    sequence_order: int


class PlannedStopUpdate(BaseModel):
    sequence_order: int | None = None
    status: str | None = None
    membership_id: UUID | None = None


class PlannedStopResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    membership_id: UUID
    shop_id: UUID
    service_date: date
    sequence_order: int
    status: str
    visit_id: UUID | None = None
    cancelled_by: UUID | None = None
    cancelled_at: datetime | None = None
    original_membership_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
