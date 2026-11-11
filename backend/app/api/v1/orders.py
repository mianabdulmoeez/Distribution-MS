import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentMembership, CurrentUser, DBSession
from app.models.catalog import (
    DeliveryAttempt,
    DeliveryStatus,
    Order,
    OrderEvent,
    OrderLine,
    OrderStatus,
)
from app.models.territory import Shop
from app.models.user import MembershipRole

router = APIRouter(prefix="/orders", tags=["Order Lifecycle Management"])


def require_business_admin(membership: CurrentMembership):
    if membership.role != MembershipRole.business_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business admin role required",
        )
    return membership


class OrderConfirm(BaseModel):
    notes: str | None = None


class OrderDispatch(BaseModel):
    dispatch_reference: str | None = None
    notes: str | None = None


class OrderDeliver(BaseModel):
    recipient: str | None = None
    delivery_note: str | None = None


class OrderDeliveryFail(BaseModel):
    failure_reason: str


class OrderReject(BaseModel):
    rejection_reason: str


@router.get("")
async def list_orders(
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
    status_filter: str | None = None,
):
    stmt = (
        select(Order, Shop)
        .join(Shop, Order.shop_id == Shop.id)
        .where(Order.tenant_id == admin.tenant_id)
        .order_by(Order.created_at.desc())
    )
    if status_filter:
        stmt = stmt.where(Order.status == OrderStatus(status_filter))

    res = await db.execute(stmt)
    rows = res.all()
    return [
        {
            "id": str(o.id),
            "shop_name": s.name,
            "shop_address": s.address,
            "origin": o.origin.value,
            "status": o.status.value,
            "total_amount": float(o.total_amount),
            "confirmed_amount": float(o.confirmed_amount) if o.confirmed_amount else None,
            "is_urgent": o.is_urgent,
            "created_at": o.created_at,
        }
        for o, s in rows
    ]


@router.get("/{order_id}")
async def get_order_detail(
    order_id: uuid.UUID,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    o_res = await db.execute(
        select(Order, Shop)
        .join(Shop, Order.shop_id == Shop.id)
        .where(Order.id == order_id, Order.tenant_id == admin.tenant_id)
    )
    row = o_res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order, shop = row

    lines_res = await db.execute(
        select(OrderLine).where(OrderLine.order_id == order.id)
    )
    lines = lines_res.scalars().all()

    events_res = await db.execute(
        select(OrderEvent).where(OrderEvent.order_id == order.id).order_by(OrderEvent.created_at)
    )
    events = events_res.scalars().all()

    return {
        "id": str(order.id),
        "shop": {"name": shop.name, "address": shop.address, "city": shop.city},
        "origin": order.origin.value,
        "status": order.status.value,
        "total_amount": float(order.total_amount),
        "confirmed_amount": float(order.confirmed_amount) if order.confirmed_amount else None,
        "is_urgent": order.is_urgent,
        "notes": order.notes,
        "created_at": order.created_at,
        "lines": [
            {
                "product_name": l.product_name,
                "sku": l.product_sku,
                "unit": l.unit,
                "unit_price": float(l.unit_price),
                "qty_requested": l.qty_requested,
                "qty_confirmed": l.qty_confirmed,
                "line_total": float(l.line_total),
            }
            for l in lines
        ],
        "events": [
            {
                "event_type": e.event_type,
                "reason": e.reason,
                "created_at": e.created_at,
            }
            for e in events
        ],
    }


@router.post("/{order_id}/confirm")
async def confirm_order(
    order_id: uuid.UUID,
    req: OrderConfirm,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    current_user: CurrentUser,
    db: DBSession,
):
    res = await db.execute(
        select(Order).where(Order.id == order_id, Order.tenant_id == admin.tenant_id)
    )
    order = res.scalar_one_or_none()
    if not order or order.status != OrderStatus.submitted:
        raise HTTPException(status_code=400, detail="Order cannot be confirmed in current state")

    order.status = OrderStatus.confirmed
    order.confirmed_amount = order.total_amount

    event = OrderEvent(
        tenant_id=admin.tenant_id,
        order_id=order.id,
        event_type="confirmed",
        actor_id=current_user.id,
        reason=req.notes,
    )
    db.add(event)
    await db.commit()
    return {"id": str(order.id), "status": order.status.value}


@router.post("/{order_id}/dispatch")
async def dispatch_order(
    order_id: uuid.UUID,
    req: OrderDispatch,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    current_user: CurrentUser,
    db: DBSession,
):
    res = await db.execute(
        select(Order).where(Order.id == order_id, Order.tenant_id == admin.tenant_id)
    )
    order = res.scalar_one_or_none()
    if not order or order.status not in (OrderStatus.confirmed, OrderStatus.delivery_failed):
        raise HTTPException(status_code=400, detail="Order cannot be dispatched")

    order.status = OrderStatus.dispatched
    now = datetime.now(timezone.utc)

    # Record delivery attempt
    attempt = DeliveryAttempt(
        tenant_id=admin.tenant_id,
        order_id=order.id,
        attempt_number=1,
        dispatched_by=current_user.id,
        dispatched_at=now,
        dispatch_reference=req.dispatch_reference,
        status=DeliveryStatus.dispatched,
    )
    db.add(attempt)

    event = OrderEvent(
        tenant_id=admin.tenant_id,
        order_id=order.id,
        event_type="dispatched",
        actor_id=current_user.id,
        reason=req.notes,
    )
    db.add(event)
    await db.commit()
    return {"id": str(order.id), "status": order.status.value}


@router.post("/{order_id}/deliver")
async def mark_delivered(
    order_id: uuid.UUID,
    req: OrderDeliver,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    current_user: CurrentUser,
    db: DBSession,
):
    res = await db.execute(
        select(Order).where(Order.id == order_id, Order.tenant_id == admin.tenant_id)
    )
    order = res.scalar_one_or_none()
    if not order or order.status != OrderStatus.dispatched:
        raise HTTPException(status_code=400, detail="Order must be in dispatched state")

    order.status = OrderStatus.delivered
    now = datetime.now(timezone.utc)

    event = OrderEvent(
        tenant_id=admin.tenant_id,
        order_id=order.id,
        event_type="delivered",
        actor_id=current_user.id,
        reason=f"Delivered to {req.recipient or 'shop'}",
    )
    db.add(event)
    await db.commit()
    return {"id": str(order.id), "status": order.status.value}


@router.post("/{order_id}/delivery-failed")
async def mark_delivery_failed(
    order_id: uuid.UUID,
    req: OrderDeliveryFail,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    current_user: CurrentUser,
    db: DBSession,
):
    res = await db.execute(
        select(Order).where(Order.id == order_id, Order.tenant_id == admin.tenant_id)
    )
    order = res.scalar_one_or_none()
    if not order or order.status != OrderStatus.dispatched:
        raise HTTPException(status_code=400, detail="Order must be dispatched to fail delivery")

    order.status = OrderStatus.delivery_failed

    event = OrderEvent(
        tenant_id=admin.tenant_id,
        order_id=order.id,
        event_type="delivery_failed",
        actor_id=current_user.id,
        reason=req.failure_reason,
    )
    db.add(event)
    await db.commit()
    return {"id": str(order.id), "status": order.status.value}

