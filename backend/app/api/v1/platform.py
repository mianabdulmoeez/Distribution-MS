import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_db
from app.core.security import hash_password
from app.models.tenant import Tenant, TenantStatus
from app.models.user import Membership, MembershipRole, MembershipStatus, User

router = APIRouter(prefix="/platform", tags=["Platform Super Admin"])


def require_platform_admin(current_user: CurrentUser):
    if not current_user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform super admin privilege required",
        )
    return current_user


class BusinessCreate(BaseModel):
    business_name: str
    business_code: str
    city: str
    contact_name: str
    contact_phone: str
    owner_email: str
    timezone: str = "Asia/Karachi"


class BusinessStatusUpdate(BaseModel):
    status: str  # active, rejected, suspended


class TenantUserProvision(BaseModel):
    full_name: str
    username: str
    password: str
    role: str = "business_admin"  # business_admin, salesperson
    phone: str | None = None
    email: str | None = None


@router.post("/businesses")
async def create_business(
    req: BusinessCreate,
    current_user: Annotated[CurrentUser, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Check if business code already exists
    existing = await db.execute(
        select(Tenant).where(Tenant.business_code == req.business_code.upper())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Business code {req.business_code.upper()} already exists",
        )

    tenant = Tenant(
        business_name=req.business_name,
        business_code=req.business_code.upper(),
        city=req.city,
        contact_name=req.contact_name,
        contact_phone=req.contact_phone,
        owner_email=req.owner_email,
        timezone=req.timezone,
        status=TenantStatus.active,  # platform admin direct provisioning creates active business
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    return {
        "id": str(tenant.id),
        "business_name": tenant.business_name,
        "business_code": tenant.business_code,
        "city": tenant.city,
        "status": tenant.status.value,
        "created_at": tenant.created_at,
    }


@router.get("/businesses")
async def list_businesses(
    current_user: Annotated[CurrentUser, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(Tenant).order_by(Tenant.created_at.desc())
    res = await db.execute(stmt)
    tenants = res.scalars().all()
    return [
        {
            "id": str(t.id),
            "business_name": t.business_name,
            "business_code": t.business_code,
            "city": t.city,
            "status": t.status.value,
            "contact_name": t.contact_name,
            "contact_phone": t.contact_phone,
            "owner_email": t.owner_email,
            "created_at": t.created_at,
        }
        for t in tenants
    ]


@router.patch("/businesses/{tenant_id}")
async def update_business_status(
    tenant_id: uuid.UUID,
    req: BusinessStatusUpdate,
    current_user: Annotated[CurrentUser, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    try:
        tenant.status = TenantStatus(req.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    await db.commit()
    return {"id": str(tenant.id), "status": tenant.status.value}


@router.post("/businesses/{tenant_id}/users")
async def provision_tenant_user(
    tenant_id: uuid.UUID,
    req: TenantUserProvision,
    current_user: Annotated[CurrentUser, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    # Check username per tenant
    m_check = await db.execute(
        select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.username == req.username.lower(),
        )
    )
    if m_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username {req.username} already exists in this tenant",
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

    role_enum = MembershipRole(req.role)
    membership = Membership(
        user_id=user.id,
        tenant_id=tenant_id,
        username=req.username.lower(),
        role=role_enum,
        status=MembershipStatus.active,
    )
    db.add(membership)
    await db.commit()

    return {
        "user_id": str(user.id),
        "membership_id": str(membership.id),
        "username": membership.username,
        "role": membership.role.value,
        "tenant_id": str(tenant_id),
    }

