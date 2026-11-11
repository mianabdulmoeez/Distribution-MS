from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --- Location verification schemas ---
class CheckInRequest(BaseModel):
    shop_id: UUID
    lat: float
    lng: float
    accuracy_meters: float
    fix_age_seconds: float
    is_mock: bool = False
    device_monotonic_time: int | None = None


class CheckInResponse(BaseModel):
    visit_id: UUID
    grant_id: UUID
    challenge_token: str
    grant_expires_at: datetime
    distance_meters: float
    message: str = "Check-in verified successfully"


class OrderLineInput(BaseModel):
    product_id: UUID
    qty_requested: int = Field(gt=0)


class CustomRequestInput(BaseModel):
    item_description: str
    quantity: str | None = None
    requirements: str | None = None
    priority: str = "normal"  # normal, urgent
    requested_by_time: datetime | None = None
    callback_phone: str | None = None
    callback_note: str | None = None


class VisitSubmitRequest(BaseModel):
    visit_id: UUID
    grant_id: UUID
    outcome: str  # order_placed, no_order, shop_closed, contact_unavailable, custom_request_only
    no_order_reason: str | None = None  # sufficient_stock, price_objection, credit_issue, other
    notes: str | None = None
    lat: float
    lng: float
    accuracy_meters: float
    fix_age_seconds: float
    is_mock: bool = False
    idempotency_key: str
    order_lines: list[OrderLineInput] = []
    custom_request: CustomRequestInput | None = None


class VisitResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    membership_id: UUID
    shop_id: UUID
    planned_stop_id: UUID | None = None
    outcome: str
    no_order_reason: str | None = None
    notes: str | None = None
    check_in_at: datetime
    submitted_at: datetime | None = None
    submit_distance: float | None = None
    is_verified: bool
    is_ad_hoc: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class VisitSubmitResponse(BaseModel):
    visit: VisitResponse
    order_id: UUID | None = None
    custom_request_id: UUID | None = None
    message: str = "Visit outcome submitted successfully"

