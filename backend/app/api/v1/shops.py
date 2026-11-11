import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentMembership, DBSession
from app.models.territory import Area, Shop, ShopLocationVersion, ShopStatus
from app.models.user import MembershipRole

router = APIRouter(prefix="/shops", tags=["Shops Management"])


def require_business_admin(membership: CurrentMembership):
    if membership.role != MembershipRole.business_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business admin role required",
        )
    return membership


class ShopCreateDirect(BaseModel):
    area_id: uuid.UUID
    name: str
    contact_person: str | None = None
    contact_phone: str | None = None
    address: str
    landmark: str | None = None
    city: str
    entrance_lat: float
    entrance_lng: float
    entrance_pin: str
    radius_meters: float = 10.0


class ShopApproval(BaseModel):
    entrance_lat: float | None = None
    entrance_lng: float | None = None
    radius_meters: float | None = None


class ShopReject(BaseModel):
    rejection_reason: str


@router.post("")
async def create_shop(
    req: ShopCreateDirect,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    # Verify area belongs to tenant
    a_res = await db.execute(
        select(Area).where(Area.id == req.area_id, Area.tenant_id == admin.tenant_id)
    )
    if not a_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Area not found")

    shop = Shop(
        tenant_id=admin.tenant_id,
        area_id=req.area_id,
        name=req.name,
        contact_person=req.contact_person,
        contact_phone=req.contact_phone,
        address=req.address,
        landmark=req.landmark,
        city=req.city,
        entrance_lat=req.entrance_lat,
        entrance_lng=req.entrance_lng,
        entrance_pin=req.entrance_pin,
        radius_meters=req.radius_meters,
        status=ShopStatus.approved,  # Direct admin creation is pre-approved
        approved_by=admin.user_id,
        approved_at=datetime.now(timezone.utc),
        pin_version=1,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    # Record initial location version
    loc_v = ShopLocationVersion(
        shop_id=shop.id,
        tenant_id=admin.tenant_id,
        version=1,
        lat=req.entrance_lat,
        lng=req.entrance_lng,
        reason="Initial creation",
        changed_by=admin.user_id,
    )
    db.add(loc_v)
    await db.commit()

    return {
        "id": str(shop.id),
        "name": shop.name,
        "area_id": str(shop.area_id),
        "status": shop.status.value,
        "entrance_pin": shop.entrance_pin,
        "entrance_lat": float(shop.entrance_lat),
        "entrance_lng": float(shop.entrance_lng),
        "radius_meters": shop.radius_meters,
    }


@router.get("")
async def list_shops(
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
    area_id: uuid.UUID | None = None,
    status_filter: str | None = None,
):
    stmt = select(Shop).where(Shop.tenant_id == admin.tenant_id)
    if area_id:
        stmt = stmt.where(Shop.area_id == area_id)
    if status_filter:
        stmt = stmt.where(Shop.status == ShopStatus(status_filter))
    stmt = stmt.order_by(Shop.name)

    res = await db.execute(stmt)
    shops = res.scalars().all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "area_id": str(s.area_id),
            "address": s.address,
            "city": s.city,
            "status": s.status.value,
            "entrance_lat": float(s.entrance_lat),
            "entrance_lng": float(s.entrance_lng),
            "entrance_pin": s.entrance_pin,
            "radius_meters": s.radius_meters,
            "contact_person": s.contact_person,
            "contact_phone": s.contact_phone,
        }
        for s in shops
    ]


@router.post("/{shop_id}/approve")
async def approve_shop(
    shop_id: uuid.UUID,
    req: ShopApproval,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    res = await db.execute(
        select(Shop).where(Shop.id == shop_id, Shop.tenant_id == admin.tenant_id)
    )
    shop = res.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    shop.status = ShopStatus.approved
    shop.approved_by = admin.user_id
    shop.approved_at = datetime.now(timezone.utc)

    if req.entrance_lat is not None and req.entrance_lng is not None:
        shop.entrance_lat = req.entrance_lat
        shop.entrance_lng = req.entrance_lng
        shop.pin_version += 1
        loc_v = ShopLocationVersion(
            shop_id=shop.id,
            tenant_id=admin.tenant_id,
            version=shop.pin_version,
            lat=req.entrance_lat,
            lng=req.entrance_lng,
            reason="Admin adjusted on approval",
            changed_by=admin.user_id,
        )
        db.add(loc_v)

    if req.radius_meters is not None:
        shop.radius_meters = req.radius_meters

    await db.commit()
    return {
        "id": str(shop.id),
        "status": shop.status.value,
        "approved_at": shop.approved_at,
        "entrance_pin": shop.entrance_pin,
    }


@router.post("/{shop_id}/reject")
async def reject_shop(
    shop_id: uuid.UUID,
    req: ShopReject,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    res = await db.execute(
        select(Shop).where(Shop.id == shop_id, Shop.tenant_id == admin.tenant_id)
    )
    shop = res.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    shop.status = ShopStatus.rejected
    shop.rejection_reason = req.rejection_reason
    await db.commit()
    return {"id": str(shop.id), "status": shop.status.value, "reason": shop.rejection_reason}


class ShopCsvRow(BaseModel):
    name: str
    area_name: str
    contact_person: str | None = None
    contact_phone: str | None = None
    address: str
    landmark: str | None = None
    city: str
    entrance_lat: float
    entrance_lng: float
    entrance_pin: str
    radius_meters: float = 10.0


class ShopImportCommitRequest(BaseModel):
    valid_rows: list[ShopCsvRow]


@router.post("/import/preview")
async def preview_shop_csv(
    file: UploadFile = File(...),
    admin: Annotated[CurrentMembership, Depends(require_business_admin)] = None,
    db: DBSession = None,
):
    """
    Spec Section 03: Provide a validated CSV import for existing shops.
    Preview invalid rows and likely duplicates. Import only rows with a valid area and pin.
    """
    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    # Fetch active areas for tenant
    area_res = await db.execute(
        select(Area).where(Area.tenant_id == admin.tenant_id, Area.is_active.is_(True))
    )
    areas_by_name = {a.name.strip().lower(): a for a in area_res.scalars().all()}

    # Fetch existing shops for duplicate checks (normalized phone or name)
    shops_res = await db.execute(select(Shop).where(Shop.tenant_id == admin.tenant_id))
    existing_shops = shops_res.scalars().all()
    existing_names = {s.name.strip().lower() for s in existing_shops}
    existing_phones = {s.contact_phone.strip() for s in existing_shops if s.contact_phone}

    valid_rows = []
    invalid_rows = []

    for idx, row in enumerate(reader, start=2):
        name = row.get("name", "").strip()
        area_name = row.get("area_name", "").strip()
        pin = row.get("entrance_pin", "").strip()
        phone = row.get("contact_phone", "").strip()

        errors = []
        if not name:
            errors.append("Missing shop name")
        if not area_name:
            errors.append("Missing area name")
        elif area_name.lower() not in areas_by_name:
            errors.append(f"Area '{area_name}' not found in active areas")
        if not pin or len(pin) < 4:
            errors.append("Entrance PIN must be at least 4 digits")

        try:
            lat = float(row.get("entrance_lat", ""))
            lng = float(row.get("entrance_lng", ""))
        except (ValueError, TypeError):
            errors.append("Invalid or missing latitude/longitude coordinates")
            lat, lng = 0.0, 0.0

        is_duplicate = False
        duplicate_reasons = []
        if name.lower() in existing_names:
            is_duplicate = True
            duplicate_reasons.append("Exact shop name duplicate")
        if phone and phone in existing_phones:
            is_duplicate = True
            duplicate_reasons.append("Shared contact phone duplicate")

        row_dict = {
            "row_number": idx,
            "name": name,
            "area_name": area_name,
            "contact_person": row.get("contact_person", "").strip() or None,
            "contact_phone": phone or None,
            "address": row.get("address", "").strip(),
            "landmark": row.get("landmark", "").strip() or None,
            "city": row.get("city", "").strip(),
            "entrance_lat": lat,
            "entrance_lng": lng,
            "entrance_pin": pin,
            "radius_meters": float(row.get("radius_meters", 10.0) or 10.0),
        }

        if errors:
            invalid_rows.append({"row": row_dict, "errors": errors})
        else:
            valid_rows.append({
                "row": row_dict,
                "is_duplicate": is_duplicate,
                "duplicate_reasons": duplicate_reasons
            })

    return {
        "total_rows": len(valid_rows) + len(invalid_rows),
        "valid_count": len(valid_rows),
        "invalid_count": len(invalid_rows),
        "valid_preview": valid_rows,
        "invalid_preview": invalid_rows,
    }


@router.post("/import/commit")
async def commit_shop_csv(
    req: ShopImportCommitRequest,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    """
    Explicit admin confirmation activates imported shops.
    """
    # Fetch active areas for tenant
    area_res = await db.execute(
        select(Area).where(Area.tenant_id == admin.tenant_id, Area.is_active.is_(True))
    )
    areas_by_name = {a.name.strip().lower(): a for a in area_res.scalars().all()}

    imported_shops = []
    now = datetime.now(timezone.utc)

    for item in req.valid_rows:
        area = areas_by_name.get(item.area_name.strip().lower())
        if not area:
            continue

        shop = Shop(
            tenant_id=admin.tenant_id,
            area_id=area.id,
            name=item.name,
            contact_person=item.contact_person,
            contact_phone=item.contact_phone,
            address=item.address,
            landmark=item.landmark,
            city=item.city,
            entrance_lat=item.entrance_lat,
            entrance_lng=item.entrance_lng,
            entrance_pin=item.entrance_pin,
            radius_meters=item.radius_meters,
            status=ShopStatus.approved,
            approved_by=admin.user_id,
            approved_at=now,
            pin_version=1,
        )
        db.add(shop)
        imported_shops.append(shop)

    await db.commit()
    return {
        "message": f"Successfully imported and activated {len(imported_shops)} shops.",
        "imported_count": len(imported_shops),
    }

