from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --- Product ---
class ProductCreate(BaseModel):
    name: str
    sku: str
    unit: str  # piece, pack, carton
    price_pkr: Decimal = Field(gt=0)


class ProductUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    price_pkr: Decimal | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    sku: str
    unit: str
    price_pkr: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Order Line ---
class OrderLineResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    product_sku: str
    unit: str
    unit_price: Decimal
    qty_requested: int
    qty_confirmed: int | None = None
    line_total: Decimal
    confirmed_line_total: Decimal | None = None

    model_config = {"from_attributes": True}


# --- Order ---
class OrderCreate(BaseModel):
    shop_id: UUID
    is_urgent: bool = False
    notes: str | None = None
    lines: list[dict[str, Any]] = []


class OrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    shop_id: UUID
    visit_id: UUID | None = None
    membership_id: UUID | None = None
    created_by: UUID
    origin: str
    status: str
    total_amount: Decimal
    confirmed_amount: Decimal | None = None
    is_urgent: bool
    notes: str | None = None
    rejection_reason: str | None = None
    lines: list[OrderLineResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderConfirmRequest(BaseModel):
    confirmed_lines: list[dict[str, Any]] | None = None
    notes: str | None = None


class OrderDispatch(BaseModel):
    dispatch_reference: str | None = None
    notes: str | None = None


class OrderDeliver(BaseModel):
    recipient: str | None = None
    delivery_note: str | None = None


class OrderDeliveryFailed(BaseModel):
    failure_reason: str


# --- Custom Request ---
class CustomRequestResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    shop_id: UUID
    visit_id: UUID | None = None
    membership_id: UUID | None = None
    created_by: UUID
    item_description: str
    quantity: str | None = None
    requirements: str | None = None
    priority: str
    requested_by_time: datetime | None = None
    callback_phone: str | None = None
    callback_note: str | None = None
    status: str
    assigned_to: UUID | None = None
    due_date: date | None = None
    order_id: UUID | None = None
    origin: str
    reference_id: str
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

