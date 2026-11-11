import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.core.deps import CurrentUser, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from app.models.tenant import Tenant, TenantStatus
from app.models.user import Membership, MembershipRole, MembershipStatus, Session, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    business_code: str
    username: str
    password: str
    device_info: str | None = None


class PlatformLoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=AuthResponse)
async def login(
    req: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # 1. Resolve tenant by business code (case-insensitive)
    t_stmt = select(Tenant).where(Tenant.business_code == req.business_code.upper())
    t_res = await db.execute(t_stmt)
    tenant = t_res.scalar_one_or_none()
    if not tenant or tenant.status != TenantStatus.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid business code or business inactive/suspended",
        )

    # 2. Resolve membership by tenant + username
    m_stmt = (
        select(Membership)
        .where(
            Membership.tenant_id == tenant.id,
            Membership.username == req.username.lower(),
            Membership.status == MembershipStatus.active,
        )
    )
    m_res = await db.execute(m_stmt)
    membership = m_res.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # 3. Resolve user
    u_stmt = select(User).where(User.id == membership.user_id, User.is_active.is_(True))
    u_res = await db.execute(u_stmt)
    user = u_res.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # 4. Create active session
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    session = Session(
        user_id=user.id,
        membership_id=membership.id,
        token_jti=jti,
        device_info=req.device_info,
        is_active=True,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    await db.commit()

    # 5. Generate tokens
    access_token = create_access_token(
        user_id=str(user.id),
        membership_id=str(membership.id),
        tenant_id=str(tenant.id),
        role=membership.role.value,
        jti=jti,
    )
    refresh_token = create_refresh_token(user_id=str(user.id), jti=jti)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "full_name": user.full_name,
            "username": membership.username,
            "role": membership.role.value,
            "tenant_id": str(tenant.id),
            "business_name": tenant.business_name,
            "business_code": tenant.business_code,
            "must_change_password": user.must_change_password,
        },
    )


@router.post("/login/platform", response_model=AuthResponse)
async def platform_login(
    req: PlatformLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Platform admin login directly with email or phone or username
    u_stmt = select(User).where(
        (User.email == req.username) | (User.phone == req.username),
        User.is_platform_admin.is_(True),
        User.is_active.is_(True),
    )
    u_res = await db.execute(u_stmt)
    user = u_res.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid platform credentials",
        )

    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    session = Session(
        user_id=user.id,
        token_jti=jti,
        is_active=True,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    await db.commit()

    access_token = create_access_token(
        user_id=str(user.id),
        role="platform_admin",
        jti=jti,
    )
    refresh_token = create_refresh_token(user_id=str(user.id), jti=jti)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "full_name": user.full_name,
            "role": "platform_admin",
            "is_platform_admin": True,
        },
    )


@router.post("/refresh")
async def refresh_token(
    req: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = verify_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    jti = payload.get("jti")
    sess_stmt = select(Session).where(Session.token_jti == jti, Session.is_active.is_(True))
    sess_res = await db.execute(sess_stmt)
    sess = sess_res.scalar_one_or_none()
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session revoked",
        )

    user_id = payload.get("sub")
    u_stmt = select(User).where(User.id == uuid.UUID(user_id), User.is_active.is_(True))
    u_res = await db.execute(u_stmt)
    user = u_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    membership = None
    if sess.membership_id:
        m_stmt = select(Membership).where(
            Membership.id == sess.membership_id,
            Membership.status == MembershipStatus.active,
        )
        m_res = await db.execute(m_stmt)
        membership = m_res.scalar_one_or_none()

    new_access_token = create_access_token(
        user_id=str(user.id),
        membership_id=str(membership.id) if membership else None,
        tenant_id=str(membership.tenant_id) if membership else None,
        role=membership.role.value if membership else "platform_admin",
        jti=jti,
    )

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = getattr(current_user, "_token_payload", {})
    jti = payload.get("jti")
    if jti:
        sess_stmt = select(Session).where(Session.token_jti == jti)
        sess_res = await db.execute(sess_stmt)
        sess = sess_res.scalar_one_or_none()
        if sess:
            sess.is_active = False
            await db.commit()
    return {"message": "Successfully logged out"}
