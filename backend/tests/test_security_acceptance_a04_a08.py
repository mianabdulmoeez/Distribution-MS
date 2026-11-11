import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append("F:\\DMS\\backend")

from app.main import app
from app.seed import init_db_and_seed


@pytest.mark.asyncio
async def test_acceptance_a04_and_a08():
    await init_db_and_seed()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:

        # ----------------------------------------------------------------------
        # A04 Test 1: Unassigned shop blocks field check-in
        # Salesman 1 is assigned only to Saddar Market.
        # Madina Super Mart is in Saddar.
        # Lahore Fancy Store is in Lahore (different tenant and area).
        # Gulshan area shops have no assignment for Salesman 1.
        # ----------------------------------------------------------------------
        sp_login = await client.post(
            "/api/v1/auth/login",
            json={"business_code": "ALNOOR", "username": "salesman1", "password": "pass123"},
        )
        assert sp_login.status_code == 200
        sp_token = sp_login.json()["access_token"]
        sp_headers = {"Authorization": f"Bearer {sp_token}"}

        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"business_code": "ALNOOR", "username": "admin", "password": "admin123"},
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # Find Gulshan Area
        areas_res = await client.get("/api/v1/areas", headers=admin_headers)
        gulshan_area = next(a for a in areas_res.json() if "Gulshan" in a["name"])

        # Create shop in Gulshan
        gulshan_shop_res = await client.post(
            "/api/v1/shops",
            json={
                "area_id": gulshan_area["id"],
                "name": "Gulshan Corner Store",
                "address": "Block 13D, Gulshan",
                "city": "Karachi",
                "entrance_lat": 24.9200000,
                "entrance_lng": 67.0800000,
                "entrance_pin": "1122",
                "radius_meters": 10.0,
            },
            headers=admin_headers,
        )
        assert gulshan_shop_res.status_code == 200
        gulshan_shop_id = gulshan_shop_res.json()["id"]

        # Salesperson 1 attempts check-in at Gulshan Corner Store (Not assigned!)
        unassigned_checkin = await client.post(
            "/api/v1/field/check-in",
            json={
                "shop_id": gulshan_shop_id,
                "lat": 24.9200000,
                "lng": 67.0800000,
                "accuracy_meters": 4.0,
                "fix_age_seconds": 1.0,
                "is_mock": False,
            },
            headers=sp_headers,
        )
        assert unassigned_checkin.status_code == 403
        assert "not assigned" in unassigned_checkin.json()["detail"].lower()

        # ----------------------------------------------------------------------
        # A04 Test 2: Mock location signal blocks check-in
        # ----------------------------------------------------------------------
        shops_res = await client.get("/api/v1/field/shops", headers=sp_headers)
        bismillah_shop = next(s for s in shops_res.json() if "Bismillah" in s["name"])
        mock_checkin = await client.post(
            "/api/v1/field/check-in",
            json={
                "shop_id": bismillah_shop["id"],
                "lat": 24.8607000,
                "lng": 67.0011000,
                "accuracy_meters": 4.0,
                "fix_age_seconds": 1.0,
                "is_mock": True,  # Flagged mock location
            },
            headers=sp_headers,
        )
        assert mock_checkin.status_code == 422
        assert "mock" in mock_checkin.json()["detail"].lower()

        # ----------------------------------------------------------------------
        # A04 Test 3: Stale GPS fix (>30s) blocks check-in
        # ----------------------------------------------------------------------
        stale_checkin = await client.post(
            "/api/v1/field/check-in",
            json={
                "shop_id": bismillah_shop["id"],
                "lat": 24.8607000,
                "lng": 67.0011000,
                "accuracy_meters": 4.0,
                "fix_age_seconds": 45.0,  # 45 seconds old > 30s limit
                "is_mock": False,
            },
            headers=sp_headers,
        )
        assert stale_checkin.status_code == 422
        assert "stale" in stale_checkin.json()["detail"].lower()

        # ----------------------------------------------------------------------
        # A08 Test: Session revocation blocks pending writes and active token access
        # ----------------------------------------------------------------------
        logout_res = await client.post("/api/v1/auth/logout", headers=sp_headers)
        assert logout_res.status_code == 200

        # Attempting further API calls with the revoked session token fails with 401
        revoked_call = await client.get("/api/v1/field/today", headers=sp_headers)
        assert revoked_call.status_code == 401
        assert "Session revoked" in revoked_call.json()["detail"]

