import enum
import uuid

from sqlalchemy import DateTime, Enum, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class TenantStatus(str, enum.Enum):
    pending_review = "pending_review"
    active = "active"
    rejected = "rejected"
    suspended = "suspended"


class Tenant(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "tenants"

    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    owner_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Karachi", server_default="Asia/Karachi")
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, name="tenant_status"),
        default=TenantStatus.pending_review,
        server_default="pending_review",
    )
