import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class ChallengeType(str, enum.Enum):
    check_in = "check_in"
    submission = "submission"


class CheckResult(str, enum.Enum):
    accepted = "accepted"
    rejected_distance = "rejected_distance"
    rejected_accuracy = "rejected_accuracy"
    rejected_stale = "rejected_stale"
    rejected_mock = "rejected_mock"
    rejected_expired = "rejected_expired"
    rejected_other = "rejected_other"


class VisitOutcome(str, enum.Enum):
    order_placed = "order_placed"
    no_order = "no_order"
    shop_closed = "shop_closed"
    contact_unavailable = "contact_unavailable"
    custom_request_only = "custom_request_only"


class ExceptionStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class LocationChallenge(Base, UUIDPrimaryKey):
    __tablename__ = "location_challenges"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memberships.id"), nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False
    )
    challenge_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    challenge_type: Mapped[ChallengeType] = mapped_column(
        Enum(ChallengeType, name="challenge_type"), nullable=False
    )
    is_consumed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
    )


class VisitGrant(Base, UUIDPrimaryKey):
    __tablename__ = "visit_grants"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memberships.id"), nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False
    )
    visit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visits.id", use_alter=True), nullable=False
    )
    pin_version: Mapped[int] = mapped_column(Integer, nullable=False)
    check_challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("location_challenges.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
    )


class CheckAttempt(Base, UUIDPrimaryKey):
    __tablename__ = "check_attempts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memberships.id"), nullable=False
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("location_challenges.id"), nullable=False
    )
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    accuracy_meters: Mapped[float] = mapped_column(Float, nullable=False)
    fix_age_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    result: Mapped[CheckResult] = mapped_column(
        Enum(CheckResult, name="check_result"), nullable=False
    )
    reason_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    policy_version: Mapped[str] = mapped_column(String(20), default="v1", server_default="v1")
    radius_used: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
    )


class Visit(Base, UUIDPrimaryKey):
    __tablename__ = "visits"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memberships.id"), nullable=False
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False
    )
    planned_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("planned_stops.id"), nullable=True
    )
    visit_grant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    outcome: Mapped[VisitOutcome | None] = mapped_column(
        Enum(VisitOutcome, name="visit_outcome"), nullable=True
    )
    no_order_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    check_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submit_lat: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    submit_lng: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    submit_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    submit_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_ad_hoc: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
    )


class VisitException(Base, UUIDPrimaryKey):
    __tablename__ = "visit_exceptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    visit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visits.id"), nullable=True
    )
    check_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("check_attempts.id"), nullable=True
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memberships.id"), nullable=False
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False
    )
    exception_type: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ExceptionStatus] = mapped_column(
        Enum(ExceptionStatus, name="exception_status"),
        default=ExceptionStatus.open,
        server_default="open",
    )
    closed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False,
    )
