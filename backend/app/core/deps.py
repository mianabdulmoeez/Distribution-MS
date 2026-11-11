from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import verify_token
from app.models.tenant import Tenant, TenantStatus
from app.models.user import Membership, MembershipStatus, Session, User

security_scheme = HTTPBearer()


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async for session in get_async_session():
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: DBSession,
) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    jti = payload.get("jti")
    if jti:
        sess_result = await db.execute(
            select(Session).where(Session.token_jti == jti, Session.is_active.is_(True))
        )
        sess = sess_result.scalar_one_or_none()
        if sess is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session revoked",
            )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    # Attach token payload for downstream use
    user._token_payload = payload  # type: ignore[attr-defined]
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_membership(
    user: CurrentUser,
    db: DBSession,
) -> Membership:
    payload = getattr(user, "_token_payload", {})
    membership_id = payload.get("membership_id")
    if not membership_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No membership context in token",
        )
    result = await db.execute(
        select(Membership).where(
            Membership.id == UUID(membership_id),
            Membership.user_id == user.id,
            Membership.status == MembershipStatus.active,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Membership not found or inactive",
        )
    return membership


CurrentMembership = Annotated[Membership, Depends(get_current_membership)]


async def get_tenant(
    membership: CurrentMembership,
    db: DBSession,
) -> Tenant:
    result = await db.execute(
        select(Tenant).where(Tenant.id == membership.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None or tenant.status != TenantStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant not found or not active",
        )
    return tenant


CurrentTenant = Annotated[Tenant, Depends(get_tenant)]


def require_role(*roles: str):
    async def _check(membership: CurrentMembership) -> Membership:
        if membership.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(roles)}",
            )
        return membership
    return Depends(_check)


def require_platform_admin():
    async def _check(user: CurrentUser) -> User:
        if not user.is_platform_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Platform admin access required",
            )
        return user
    return Depends(_check)
