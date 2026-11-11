import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentMembership, DBSession
from app.core.security import hash_password
from app.models.territory import Area, AreaAssignment, Shop
from app.models.user import Membership, MembershipRole, MembershipStatus, User

router = APIRouter(tags=["Business Admin Management"])


def require_business_admin(membership: CurrentMembership):
    if membership.role != MembershipRole.business_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business admin role required",
        )
    return membership


# --- Areas ---
class AreaCreate(BaseModel):
    name: str
    description: str | None = None


class AreaAssignmentCreate(BaseModel):
    membership_id: uuid.UUID
    start_date: date | None = None
    end_date: date | None = None


@router.post("/areas")
async def create_area(
    req: AreaCreate,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    area = Area(
        tenant_id=admin.tenant_id,
        name=req.name,
        description=req.description,
        is_active=True,
    )
    db.add(area)
    await db.commit()
    await db.refresh(area)
    return {
        "id": str(area.id),
        "name": area.name,
        "description": area.description,
        "is_active": area.is_active,
    }


@router.get("/areas")
async def list_areas(
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    stmt = (
        select(Area)
        .where(Area.tenant_id == admin.tenant_id, Area.is_active.is_(True))
        .order_by(Area.name)
    )
    res = await db.execute(stmt)
    areas = res.scalars().all()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "description": a.description,
            "is_active": a.is_active,
        }
        for a in areas
    ]


@router.post("/areas/{area_id}/assignments")
async def assign_salesperson_to_area(
    area_id: uuid.UUID,
    req: AreaAssignmentCreate,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    # Verify area belongs to tenant
    a_res = await db.execute(
        select(Area).where(Area.id == area_id, Area.tenant_id == admin.tenant_id)
    )
    area = a_res.scalar_one_or_none()
    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found")

    # Verify salesperson membership belongs to tenant
    m_res = await db.execute(
        select(Membership).where(
            Membership.id == req.membership_id,
            Membership.tenant_id == admin.tenant_id,
            Membership.role == MembershipRole.salesperson,
        )
    )
    salesperson = m_res.scalar_one_or_none()
    if not salesperson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salesperson not found")

    assignment = AreaAssignment(
        tenant_id=admin.tenant_id,
        area_id=area_id,
        membership_id=req.membership_id,
        start_date=req.start_date,
        end_date=req.end_date,
        is_active=True,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    return {
        "id": str(assignment.id),
        "area_id": str(assignment.area_id),
        "membership_id": str(assignment.membership_id),
        "is_active": assignment.is_active,
    }


# --- Salespeople Management ---
class SalespersonCreate(BaseModel):
    full_name: str
    username: str
    password: str
    phone: str | None = None
    email: str | None = None


@router.post("/users")
async def create_salesperson(
    req: SalespersonCreate,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    # Verify username uniqueness per tenant
    m_check = await db.execute(
        select(Membership).where(
            Membership.tenant_id == admin.tenant_id,
            Membership.username == req.username.lower(),
        )
    )
    if m_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username {req.username} already exists in your organization",
        )

    user = User(
        full_name=req.full_name,
        email=req.email,
        phone=req.phone,
        password_hash=hash_password(req.password),
        is_platform_admin=False,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    membership = Membership(
        user_id=user.id,
        tenant_id=admin.tenant_id,
        username=req.username.lower(),
        role=MembershipRole.salesperson,
        status=MembershipStatus.active,
    )
    db.add(membership)
    await db.commit()

    return {
        "user_id": str(user.id),
        "membership_id": str(membership.id),
        "username": membership.username,
        "full_name": user.full_name,
        "role": membership.role.value,
    }


@router.get("/users")
async def list_salespeople(
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    stmt = (
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(
            Membership.tenant_id == admin.tenant_id,
            Membership.role == MembershipRole.salesperson,
        )
    )
    res = await db.execute(stmt)
    results = res.all()
    return [
        {
            "membership_id": str(m.id),
            "user_id": str(u.id),
            "username": m.username,
            "full_name": u.full_name,
            "phone": u.phone,
            "status": m.status.value,
        }
        for m, u in results
    ]

