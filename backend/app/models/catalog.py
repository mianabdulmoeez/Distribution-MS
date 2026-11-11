import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class OrderOrigin(str, enum.Enum):
    field = "field"
    office = "office"
    custom_request_conversion = "custom_request_conversion"


class OrderStatus(str, enum.Enum):
    submitted = "submitted"
    confirmed = "confirmed"
    dispatched = "dispatched"
    delivered = "delivered"
    delivery_failed = "delivery_failed"
    rejected = "rejected"
    cancelled = "cancelled"
    closed_undelivered = "closed_undelivered"


class DeliveryStatus(str, enum.Enum):
    dispatched = "dispatched"
    delivered = "delivered"
    failed = "failed"


class RequestPriority(str, enum.Enum):
    normal = "normal"
    urgent = "urgent"


class RequestStatus(str, enum.Enum):
    new = "new"
    in_review = "in_review"
    converted = "converted"
    declined = "declined"
    closed = "closed"


class RequestOrigin(str, enum.Enum):
    field = "field"
    office = "office"


class Product(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "products"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    price_pkr: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Order(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "orders"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False
    )
    visit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visits.id"), nullable=True
    )
    membership_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memberships.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    origin: Mapped[OrderOrigin] = mapped_column(
        Enum(OrderOrigin, name="order_origin"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        default=OrderStatus.submitted,
        server_default="submitted",
    )
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    confirmed_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)


class OrderLine(Base, UUIDPrimaryKey):
    __tablename__ = "order_lines"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    qty_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_confirmed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    confirmed_line_total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
    )


class OrderEvent(Base, UUIDPrimaryKey):
    __tablename__ = "order_events"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
    )


class DeliveryAttempt(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "delivery_attempts"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    dispatched_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    dispatched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dispatch_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status"),
        default=DeliveryStatus.dispatched,
        server_default="dispatched",
    )
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)


class CustomRequest(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "custom_requests"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False
    )
    visit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visits.id"), nullable=True
    )
    membership_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memberships.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    item_description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requirements: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    priority: Mapped[RequestPriority] = mapped_column(
        Enum(RequestPriority, name="request_priority"),
        default=RequestPriority.normal,
        server_default="normal",
    )
    requested_by_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    callback_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    callback_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status"),
        default=RequestStatus.new,
        server_default="new",
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True
    )
    origin: Mapped[RequestOrigin] = mapped_column(
        Enum(RequestOrigin, name="request_origin"), nullable=False
    )
    reference_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
