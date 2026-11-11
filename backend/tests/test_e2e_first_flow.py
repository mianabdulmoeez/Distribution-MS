import sys
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append("F:\\DMS\\backend")

from app.core.database import AsyncSessionLocal
from app.main import app
from app.models.tenant import Tenant
from app.models.territory import Shop


@pytest.mark.asyncio
async def test_end_to_end_flow_and_acceptance():
    from app.seed import init_db_and_seed
    await init_db_and_seed()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:

        # ----------------------------------------------------------------------
        # STEP 1: Platform Admin Provisions a New Distributor (Spec Section 02)
        # ----------------------------------------------------------------------
        platform_login_res = await client.post(
            "/api/v1/auth/login/platform",
            json={"username": "superadmin@dms.pk", "password": "admin123"},
        )
        assert platform_login_res.status_code == 200, platform_login_res.text
        super_token = platform_login_res.json()["access_token"]
        super_headers = {"Authorization": f"Bearer {super_token}"}

        # Provision New Distributor: Khyber Logistics (KHYBER)
        biz_res = await client.post(
            "/api/v1/platform/businesses",
            json={
                "business_name": "Khyber Logistics",
                "business_code": "KHYBER",
                "city": "Peshawar",
                "contact_name": "Hamza Khan",
                "contact_phone": "+923009988776",
                "owner_email": "hamza@khyber.pk",
            },
            headers=super_headers,
        )
        assert biz_res.status_code == 200, biz_res.text
        khyber_id = biz_res.json()["id"]

        # Provision Business Admin for Khyber
        admin_prov_res = await client.post(
            f"/api/v1/platform/businesses/{khyber_id}/users",
            json={
                "full_name": "Hamza Khan",
                "username": "admin",
                "password": "khyber_password_123",
                "role": "business_admin",
                "phone": "+923009988776",
            },
            headers=super_headers,
        )
        assert admin_prov_res.status_code == 200, admin_prov_res.text

        # ----------------------------------------------------------------------
        # STEP 2: Distributor Admin Signs in, Creates Area, Assigns Salesperson
        # ----------------------------------------------------------------------
        admin_login_res = await client.post(
            "/api/v1/auth/login",
            json={
                "business_code": "ALNOOR",
                "username": "admin",
                "password": "admin123",
            },
        )
        assert admin_login_res.status_code == 200, admin_login_res.text
        admin_token = admin_login_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Admin creates Area: Tariq Road
        area_res = await client.post(
            "/api/v1/areas",
            json={"name": "Tariq Road Market", "description": "Fashion & Commercial district"},
            headers=admin_headers,
        )
        assert area_res.status_code == 200, area_res.text
        tariq_area_id = area_res.json()["id"]

        # Admin creates salesperson: Tariq Salesperson 2
        sp_create_res = await client.post(
            "/api/v1/users",
            json={
                "full_name": "Kashif Salesperson",
                "username": "kashif",
                "password": "kashif_password_123",
                "phone": "+923129876543",
            },
            headers=admin_headers,
        )
        assert sp_create_res.status_code == 200, sp_create_res.text
        kashif_membership_id = sp_create_res.json()["membership_id"]

        # Assign salesperson to Tariq Road
        asgn_res = await client.post(
            f"/api/v1/areas/{tariq_area_id}/assignments",
            json={"membership_id": kashif_membership_id},
            headers=admin_headers,
        )
        assert asgn_res.status_code == 200, asgn_res.text

        # ----------------------------------------------------------------------
        # STEP 3: Admin Creates/Approves Shop with Entrance PIN (Spec Section 03)
        # Coordinates: 24.8715000, 67.0595000 (Tariq Road, Karachi)
        # ----------------------------------------------------------------------
        shop_res = await client.post(
            "/api/v1/shops",
            json={
                "area_id": tariq_area_id,
                "name": "Al-Rehman Departmental Store",
                "contact_person": "Rehman Sb",
                "contact_phone": "+923331122334",
                "address": "Tariq Road, Block 2, PECHS",
                "landmark": "Near Rabi Center",
                "city": "Karachi",
                "entrance_lat": 24.8715000,
                "entrance_lng": 67.0595000,
                "entrance_pin": "5678",
                "radius_meters": 10.0,
            },
            headers=admin_headers,
        )
        assert shop_res.status_code == 200, shop_res.text
        shop_data = shop_res.json()
        shop_id = shop_data["id"]
        assert shop_data["status"] == "approved"
        assert shop_data["entrance_pin"] == "5678"

        # ----------------------------------------------------------------------
        # STEP 4: Salesperson signs in on Mobile App (Spec Section 05)
        # ----------------------------------------------------------------------
        sp_login_res = await client.post(
            "/api/v1/auth/login",
            json={
                "business_code": "ALNOOR",
                "username": "kashif",
                "password": "kashif_password_123",
            },
        )
        assert sp_login_res.status_code == 200, sp_login_res.text
        sp_token = sp_login_res.json()["access_token"]
        sp_headers = {"Authorization": f"Bearer {sp_token}"}

        # Salesperson opens assigned shops list
        assigned_shops_res = await client.get("/api/v1/field/shops", headers=sp_headers)
        assert assigned_shops_res.status_code == 200, assigned_shops_res.text
        assigned_shops = assigned_shops_res.json()
        assert any(s["id"] == shop_id for s in assigned_shops)

        # ----------------------------------------------------------------------
        # STEP 5: Location Verification Tests (Acceptance Test A03 & Out of Radius)
        # ----------------------------------------------------------------------
        # 5a. Out of radius check-in attempt (Shop is at 24.8715, 67.0595; Fix is at 24.8900 - ~2km away)
        bad_checkin = await client.post(
            "/api/v1/field/check-in",
            json={
                "shop_id": shop_id,
                "lat": 24.8900000,
                "lng": 67.0595000,
                "accuracy_meters": 5.0,
                "fix_age_seconds": 2.0,
                "is_mock": False,
            },
            headers=sp_headers,
        )
        assert bad_checkin.status_code == 422, "Out of radius must fail with 422"
        assert "Out of radius" in bad_checkin.json()["detail"]

        # 5b. In radius check-in attempt (Exactly at entrance pin coordinates: 24.8715000, 67.0595000)
        good_checkin = await client.post(
            "/api/v1/field/check-in",
            json={
                "shop_id": shop_id,
                "lat": 24.8715000,
                "lng": 67.0595000,
                "accuracy_meters": 4.5,
                "fix_age_seconds": 1.5,
                "is_mock": False,
            },
            headers=sp_headers,
        )
        assert good_checkin.status_code == 200, good_checkin.text
        checkin_data = good_checkin.json()
        visit_id = checkin_data["visit_id"]
        grant_id = checkin_data["grant_id"]
        assert checkin_data["distance_meters"] <= 10.0

        # ----------------------------------------------------------------------
        # STEP 6: Salesperson Submits "No order" Outcome (Spec Section 05)
        # With fresh location check at submission
        # ----------------------------------------------------------------------
        # 6a. Attempt to submit from remote location fails!
        bad_submit = await client.post(
            "/api/v1/field/submit",
            json={
                "visit_id": visit_id,
                "grant_id": grant_id,
                "outcome": "no_order",
                "no_order_reason": "sufficient_stock",
                "notes": "Shopkeeper has enough tea and ketchup inventory for next 10 days.",
                "lat": 24.8900000,  # Out of radius!
                "lng": 67.0595000,
                "accuracy_meters": 4.0,
                "fix_age_seconds": 2.0,
                "is_mock": False,
                "idempotency_key": "unique-submit-key-001",
            },
            headers=sp_headers,
        )
        assert bad_submit.status_code == 422, "Remote submission must fail location verification"

        # 6b. Submit at shop pin within 10m radius
        good_submit = await client.post(
            "/api/v1/field/submit",
            json={
                "visit_id": visit_id,
                "grant_id": grant_id,
                "outcome": "no_order",
                "no_order_reason": "sufficient_stock",
                "notes": "Verified visit: shopkeeper has enough stock.",
                "lat": 24.8715020,  # Just 0.2m away from entrance pin!
                "lng": 67.0595010,
                "accuracy_meters": 3.8,
                "fix_age_seconds": 1.2,
                "is_mock": False,
                "idempotency_key": "unique-submit-key-001",
            },
            headers=sp_headers,
        )
        assert good_submit.status_code == 200, good_submit.text
        submit_data = good_submit.json()
        assert submit_data["visit"]["outcome"] == "no_order"
        assert submit_data["visit"]["is_verified"] is True
        assert submit_data["visit"]["no_order_reason"] == "sufficient_stock"

        # ----------------------------------------------------------------------
        # STEP 7: Idempotency Acceptance Test (A05)
        # Retrying a submission with same idempotency key returns identical saved result
        # ----------------------------------------------------------------------
        retry_submit = await client.post(
            "/api/v1/field/submit",
            json={
                "visit_id": visit_id,
                "grant_id": grant_id,
                "outcome": "no_order",
                "no_order_reason": "sufficient_stock",
                "notes": "Verified visit: shopkeeper has enough stock.",
                "lat": 24.8715020,
                "lng": 67.0595010,
                "accuracy_meters": 3.8,
                "fix_age_seconds": 1.2,
                "is_mock": False,
                "idempotency_key": "unique-submit-key-001",
            },
            headers=sp_headers,
        )
        assert retry_submit.status_code == 200
        assert retry_submit.json()["visit"]["id"] == str(visit_id)

        # ----------------------------------------------------------------------
        # STEP 8: Distributor Sees Verified Visit on Dashboard (Spec Section 07)
        # ----------------------------------------------------------------------
        dash_res = await client.get("/api/v1/reports/dashboard", headers=admin_headers)
        assert dash_res.status_code == 200, dash_res.text
        dash_data = dash_res.json()
        assert dash_data["visits"]["total_verified"] >= 1
        assert dash_data["visits"]["no_order"] >= 1

        # Check Weekly Summary & CSV Export
        summary_res = await client.get("/api/v1/reports/weekly-summary", headers=admin_headers)
        assert summary_res.status_code == 200, summary_res.text
        assert summary_res.json()["metrics"]["distinct_verified_visits"] >= 1

        csv_res = await client.get("/api/v1/reports/export/csv", headers=admin_headers)
        assert csv_res.status_code == 200, csv_res.text
        assert "No Order Visits" in csv_res.text

        # ----------------------------------------------------------------------
        # STEP 9: Tenant Isolation Acceptance Test (A01)
        # Login as City Star Trading (CITYSTAR) and verify cannot access ALNOOR data
        # ----------------------------------------------------------------------
        citystar_login = await client.post(
            "/api/v1/auth/login",
            json={
                "business_code": "CITYSTAR",
                "username": "admin",
                "password": "admin123",
            },
        )
        assert citystar_login.status_code == 200
        citystar_token = citystar_login.json()["access_token"]
        citystar_headers = {"Authorization": f"Bearer {citystar_token}"}

        # CityStar lists areas - must NOT see ALNOOR's Tariq Road or Saddar
        cs_areas = await client.get("/api/v1/areas", headers=citystar_headers)
        assert cs_areas.status_code == 200
        cs_area_names = [a["name"] for a in cs_areas.json()]
        assert "Tariq Road Market" not in cs_area_names
        assert "Saddar Market" not in cs_area_names
        assert "Mall Road" in cs_area_names

        # CityStar lists shops - must NOT see ALNOOR's shops
        cs_shops = await client.get("/api/v1/shops", headers=citystar_headers)
        assert cs_shops.status_code == 200
        cs_shop_names = [s["name"] for s in cs_shops.json()]
        assert "Al-Rehman Departmental Store" not in cs_shop_names
        assert "Bismillah General Store" not in cs_shop_names
        assert "Lahore Fancy Store" in cs_shop_names

        print("\n============================================================")
        print("ALL ACCEPTANCE TESTS & FIRST WORKING E2E FLOW PASSED!")
        print("============================================================")
