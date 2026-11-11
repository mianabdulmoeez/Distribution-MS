import csv
import io
import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentMembership, DBSession
from app.models.catalog import Product
from app.models.user import MembershipRole

router = APIRouter(prefix="/products", tags=["Product Catalog"])


def require_business_admin(membership: CurrentMembership):
    if membership.role != MembershipRole.business_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business admin role required",
        )
    return membership


class ProductCreate(BaseModel):
    name: str
    sku: str
    unit: str  # piece, pack, carton
    price_pkr: Decimal = Field(gt=0)


@router.post("")
async def create_product(
    req: ProductCreate,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    # Verify SKU uniqueness per tenant
    existing = await db.execute(
        select(Product).where(
            Product.tenant_id == admin.tenant_id,
            Product.sku == req.sku.upper(),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU {req.sku} already exists",
        )

    prod = Product(
        tenant_id=admin.tenant_id,
        name=req.name,
        sku=req.sku.upper(),
        unit=req.unit,
        price_pkr=req.price_pkr,
        is_active=True,
    )
    db.add(prod)
    await db.commit()
    await db.refresh(prod)

    return {
        "id": str(prod.id),
        "name": prod.name,
        "sku": prod.sku,
        "unit": prod.unit,
        "price_pkr": float(prod.price_pkr),
        "is_active": prod.is_active,
    }


@router.get("")
async def list_products(
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
    search: str | None = None,
):
    stmt = (
        select(Product)
        .where(Product.tenant_id == admin.tenant_id, Product.is_active.is_(True))
        .order_by(Product.name)
    )
    if search:
        stmt = stmt.where(Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%"))

    res = await db.execute(stmt)
    prods = res.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "sku": p.sku,
            "unit": p.unit,
            "price_pkr": float(p.price_pkr),
            "is_active": p.is_active,
        }
        for p in prods
    ]


class ProductCsvRow(BaseModel):
    name: str
    sku: str
    unit: str
    price_pkr: Decimal


class ProductImportCommitRequest(BaseModel):
    valid_rows: list[ProductCsvRow]


@router.post("/import/preview")
async def preview_product_csv(
    file: UploadFile = File(...),
    admin: Annotated[CurrentMembership, Depends(require_business_admin)] = None,
    db: DBSession = None,
):
    """
    Spec Section 06: Validated CSV import for products.
    """
    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    existing_res = await db.execute(select(Product.sku).where(Product.tenant_id == admin.tenant_id))
    existing_skus = {s.upper() for s in existing_res.scalars().all()}

    valid_rows = []
    invalid_rows = []
    seen_skus = set()

    allowed_units = {"piece", "pack", "carton", "box", "bottle", "bag", "kg", "litre"}

    for idx, row in enumerate(reader, start=2):
        name = row.get("name", "").strip()
        sku = row.get("sku", "").strip().upper()
        unit = row.get("unit", "").strip().lower()
        price_str = row.get("price_pkr", "").strip()

        errors = []
        if not name:
            errors.append("Missing product name")
        if not sku:
            errors.append("Missing SKU")
        elif sku in seen_skus or sku in existing_skus:
            errors.append(f"Duplicate SKU '{sku}'")
        if not unit or unit not in allowed_units:
            errors.append(f"Invalid unit '{unit}'. Allowed: {', '.join(sorted(allowed_units))}")

        try:
            price = Decimal(price_str)
            if price <= 0:
                errors.append("Price must be greater than zero")
        except Exception:
            errors.append("Invalid PKR price format")
            price = Decimal(0)

        row_dict = {
            "row_number": idx,
            "name": name,
            "sku": sku,
            "unit": unit,
            "price_pkr": float(price),
        }

        if errors:
            invalid_rows.append({"row": row_dict, "errors": errors})
        else:
            seen_skus.add(sku)
            valid_rows.append({"row": row_dict})

    return {
        "total_rows": len(valid_rows) + len(invalid_rows),
        "valid_count": len(valid_rows),
        "invalid_count": len(invalid_rows),
        "valid_preview": valid_rows,
        "invalid_preview": invalid_rows,
    }


@router.post("/import/commit")
async def commit_product_csv(
    req: ProductImportCommitRequest,
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    imported_products = []
    for item in req.valid_rows:
        prod = Product(
            tenant_id=admin.tenant_id,
            name=item.name,
            sku=item.sku.upper(),
            unit=item.unit,
            price_pkr=item.price_pkr,
            is_active=True,
        )
        db.add(prod)
        imported_products.append(prod)

    await db.commit()
    return {
        "message": f"Successfully imported {len(imported_products)} products.",
        "imported_count": len(imported_products),
    }

