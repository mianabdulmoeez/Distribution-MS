import asyncio
import sys
from datetime import datetime, timezone

sys.path.append("F:\\DMS\\backend")

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models.base import Base
from app.models.catalog import Product
from app.models.tenant import Tenant, TenantStatus
from app.models.territory import Area, AreaAssignment, Shop, ShopLocationVersion, ShopStatus
from app.models.user import Membership, MembershipRole, MembershipStatus, User


async def init_db_and_seed():
    print("Creating all tables in SQLite database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

    async with AsyncSessionLocal() as session:
        # 1. Super Admin
        super_admin_user = User(
            full_name="Platform Super Admin",
            email="superadmin@dms.pk",
            phone="+923000000000",
            password_hash=hash_password("admin123"),
            is_platform_admin=True,
            is_active=True,
        )
        session.add(super_admin_user)
        await session.flush()
        print("Created Super Admin user")

        # 2. Tenant 1: Al-Noor Distributors (ALNOOR) - Karachi
        t1 = Tenant(
            business_name="Al-Noor Distributors",
            business_code="ALNOOR",
            city="Karachi",
            contact_name="Ahmed Malik",
            contact_phone="+923001234567",
            owner_email="ahmed@alnoor.pk",
            timezone="Asia/Karachi",
            status=TenantStatus.active,
        )
        session.add(t1)
        await session.flush()

        # Business Admin for ALNOOR
        t1_admin_user = User(
            full_name="Ahmed Malik",
            email="ahmed@alnoor.pk",
            phone="+923001234567",
            password_hash=hash_password("admin123"),
            is_platform_admin=False,
            is_active=True,
        )
        session.add(t1_admin_user)
        await session.flush()

        t1_admin_membership = Membership(
            user_id=t1_admin_user.id,
            tenant_id=t1.id,
            username="admin",
            role=MembershipRole.business_admin,
            status=MembershipStatus.active,
        )
        session.add(t1_admin_membership)

        # Salesperson 1 for ALNOOR
        sp1_user = User(
            full_name="Tariq Salesman",
            email="tariq@alnoor.pk",
            phone="+923007654321",
            password_hash=hash_password("pass123"),
            is_platform_admin=False,
            is_active=True,
        )
        session.add(sp1_user)
        await session.flush()

        sp1_membership = Membership(
            user_id=sp1_user.id,
            tenant_id=t1.id,
            username="salesman1",
            role=MembershipRole.salesperson,
            status=MembershipStatus.active,
        )
        session.add(sp1_membership)
        await session.flush()

        # Areas for ALNOOR
        area_saddar = Area(
            tenant_id=t1.id,
            name="Saddar Market",
            description="Central Commercial & Wholesale Market, Karachi",
            is_active=True,
        )
        area_gulshan = Area(
            tenant_id=t1.id,
            name="Gulshan-e-Iqbal",
            description="Block 13D and University Road Market",
            is_active=True,
        )
        session.add_all([area_saddar, area_gulshan])
        await session.flush()

        # Assign Salesperson 1 to Saddar Area
        asgn1 = AreaAssignment(
            tenant_id=t1.id,
            area_id=area_saddar.id,
            membership_id=sp1_membership.id,
            is_active=True,
        )
        session.add(asgn1)

        # Shops in Saddar (Exact coordinates in Saddar, Karachi)
        # Lat: 24.8607000, Lng: 67.0011000
        shop1 = Shop(
            tenant_id=t1.id,
            area_id=area_saddar.id,
            name="Bismillah General Store",
            contact_person="Haji Rasheed",
            contact_phone="+923121112233",
            address="Shop 14, Main Empress Market, Saddar",
            landmark="Opposite Rainbow Centre",
            city="Karachi",
            entrance_lat=24.8607000,
            entrance_lng=67.0011000,
            entrance_pin="1234",
            radius_meters=10.0,
            status=ShopStatus.approved,
            approved_by=t1_admin_user.id,
            approved_at=datetime.now(timezone.utc),
            pin_version=1,
        )
        shop2 = Shop(
            tenant_id=t1.id,
            area_id=area_saddar.id,
            name="Madina Super Mart",
            contact_person="Muhammad Aslam",
            contact_phone="+923124445566",
            address="Plot 5B, Bohri Bazaar, Saddar",
            landmark="Near Bohra Masjid",
            city="Karachi",
            entrance_lat=24.8615000,
            entrance_lng=67.0025000,
            entrance_pin="4321",
            radius_meters=10.0,
            status=ShopStatus.approved,
            approved_by=t1_admin_user.id,
            approved_at=datetime.now(timezone.utc),
            pin_version=1,
        )
        session.add_all([shop1, shop2])
        await session.flush()

        # Record Location Versions
        loc_v1 = ShopLocationVersion(
            shop_id=shop1.id,
            tenant_id=t1.id,
            version=1,
            lat=shop1.entrance_lat,
            lng=shop1.entrance_lng,
            reason="Approved with verified entrance pin",
            changed_by=t1_admin_user.id,
        )
        loc_v2 = ShopLocationVersion(
            shop_id=shop2.id,
            tenant_id=t1.id,
            version=1,
            lat=shop2.entrance_lat,
            lng=shop2.entrance_lng,
            reason="Approved with verified entrance pin",
            changed_by=t1_admin_user.id,
        )
        session.add_all([loc_v1, loc_v2])

        # Products for ALNOOR
        p1 = Product(
            tenant_id=t1.id,
            name="Tapal Danedar Tea 400g",
            sku="TAPAL-400G",
            unit="pack",
            price_pkr=650.00,
            is_active=True,
        )
        p2 = Product(
            tenant_id=t1.id,
            name="National Tomato Ketchup 800g",
            sku="NAT-KETCH-800",
            unit="piece",
            price_pkr=420.00,
            is_active=True,
        )
        p3 = Product(
            tenant_id=t1.id,
            name="Shan Biryani Masala 50g",
            sku="SHAN-BIRY-50",
            unit="carton",
            price_pkr=2400.00,
            is_active=True,
        )
        session.add_all([p1, p2, p3])

        # 3. Tenant 2: City Star Trading (CITYSTAR) - Lahore (For Tenant Isolation Tests)
        t2 = Tenant(
            business_name="City Star Trading",
            business_code="CITYSTAR",
            city="Lahore",
            contact_name="Ali Raza",
            contact_phone="+923019876543",
            owner_email="ali@citystar.pk",
            timezone="Asia/Karachi",
            status=TenantStatus.active,
        )
        session.add(t2)
        await session.flush()

        t2_admin_user = User(
            full_name="Ali Raza",
            email="ali@citystar.pk",
            phone="+923019876543",
            password_hash=hash_password("admin123"),
            is_platform_admin=False,
            is_active=True,
        )
        session.add(t2_admin_user)
        await session.flush()

        t2_admin_membership = Membership(
            user_id=t2_admin_user.id,
            tenant_id=t2.id,
            username="admin",
            role=MembershipRole.business_admin,
            status=MembershipStatus.active,
        )
        session.add(t2_admin_membership)

        area_mall = Area(
            tenant_id=t2.id,
            name="Mall Road",
            description="Lahore Commercial District",
            is_active=True,
        )
        session.add(area_mall)
        await session.flush()

        shop_lhr = Shop(
            tenant_id=t2.id,
            area_id=area_mall.id,
            name="Lahore Fancy Store",
            contact_person="Chaudhry Akram",
            contact_phone="+923009998877",
            address="Mall Road, Anarkali, Lahore",
            landmark="Near Tollinton Market",
            city="Lahore",
            entrance_lat=31.5600000,
            entrance_lng=74.3100000,
            entrance_pin="9999",
            radius_meters=10.0,
            status=ShopStatus.approved,
            approved_by=t2_admin_user.id,
            approved_at=datetime.now(timezone.utc),
            pin_version=1,
        )
        session.add(shop_lhr)

        await session.commit()
        print("Database initialized and seeded successfully!")


if __name__ == "__main__":
    asyncio.run(init_db_and_seed())

