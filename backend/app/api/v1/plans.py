import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentMembership, DBSession
from app.models.territory import PlannedStop, PlannedStopStatus, Shop
from app.models.user import MembershipRole

router = APIRouter(prefix="/plans", tags=["Daily Visit Plans"])


def require_business_admin(membership: CurrentMembership):
    if membership.role != MembershipRole.business_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business admin role required",
        )
    return membership


class StopInput(BaseModel):
    shop_id: uuid.UUID
    sequence_order: int


class CreatePlanRequest(BaseModel):
    membership_id: uuid.UUID  # salesperson
    service_date: date
    stops: list[StopInput]


@router.post("")
async def create_daily_plan(
    req: CreatePlanRequest,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    created_stops = []
    for s in req.stops:
        stop = PlannedStop(
            tenant_id=admin.tenant_id,
            membership_id=req.membership_id,
            shop_id=s.shop_id,
            service_date=req.service_date,
            sequence_order=s.sequence_order,
            status=PlannedStopStatus.scheduled,
        )
        db.add(stop)
        created_stops.append(stop)

    await db.commit()
    return {"message": f"Created {len(created_stops)} stops for {req.service_date}"}


@router.get("")
async def get_plans(
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
    service_date: date | None = None,
    salesperson_id: uuid.UUID | None = None,
):
    stmt = (
        select(PlannedStop, Shop)
        .join(Shop, PlannedStop.shop_id == Shop.id)
        .where(PlannedStop.tenant_id == admin.tenant_id)
    )
    if service_date:
        stmt = stmt.where(PlannedStop.service_date == service_date)
    if salesperson_id:
        stmt = stmt.where(PlannedStop.membership_id == salesperson_id)
    stmt = stmt.order_by(PlannedStop.service_date.desc(), PlannedStop.sequence_order)

    res = await db.execute(stmt)
    rows = res.all()
    return [
        {
            "id": str(stop.id),
            "service_date": stop.service_date,
            "sequence_order": stop.sequence_order,
            "status": stop.status.value,
            "salesperson_id": str(stop.membership_id),
            "shop_name": shop.name,
            "shop_address": shop.address,
        }
        for stop, shop in rows
    ]

