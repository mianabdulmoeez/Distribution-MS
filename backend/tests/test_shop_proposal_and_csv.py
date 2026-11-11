import io
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append("F:\\DMS\\backend")

from app.main import app
from app.seed import init_db_and_seed


@pytest.mark.asyncio
async def test_shop_proposal_approval_acceptance_a02():
    await init_db_and_seed()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Login Salesperson in ALNOOR
        sp_login = await client.post(
            "/api/v1/auth/login",
            json={"business_code": "ALNOOR", "username": "salesman1", "password": "pass123"},
        )
        assert sp_login.status_code == 200
        sp_headers = {"Authorization": f"Bearer {sp_login.json()['access_token']}"}

        # 2. Get assigned area (Saddar Market)
        shops_res = await client.get("/api/v1/field/shops", headers=sp_headers)
        assert shops_res.status_code == 200
        saddar_area_id = shops_res.json()[0]["area_id"]

        # 3. Field salesperson proposes new shop: "New Saddar Mart"
        prop_res = await client.post(
            "/api/v1/field/shops/propose",
            json={
                "area_id": saddar_area_id,
                "name": "New Saddar Mart",
                "contact_person": "Jamil",
                "contact_phone": "+923337778899",
                "address": "Bohri Bazaar, Gali 3, Saddar",
                "city": "Karachi",
                "entrance_lat": 24.8620000,
                "entrance_lng": 67.0030000,
                "accuracy_meters": 4.5,
                "entrance_pin": "7788",
            },
            headers=sp_headers,
        )
        assert prop_res.status_code == 200, prop_res.text
        prop_data = prop_res.json()
        proposed_shop_id = prop_data["shop_id"]
        assert prop_data["status"] == "pending"

        # 4. Verify shop is UNAVAILABLE for field check-in while pending
        checkin_fail = await client.post(
            "/api/v1/field/check-in",
            json={
                "shop_id": proposed_shop_id,
                "lat": 24.8620000,
                "lng": 67.0030000,
                "accuracy_meters": 4.0,
                "fix_age_seconds": 1.0,
                "is_mock": False,
            },
            headers=sp_headers,
        )
        assert checkin_fail.status_code == 400
        assert "not approved" in checkin_fail.json()["detail"]

        # 5. Distributor Admin reviews and approves the shop with entrance pin
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"business_code": "ALNOOR", "username": "admin", "password": "admin123"},
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        appr_res = await client.post(
            f"/api/v1/shops/{proposed_shop_id}/approve",
            json={"radius_meters": 10.0},
            headers=admin_headers,
        )
        assert appr_res.status_code == 200
        assert appr_res.json()["status"] == "approved"

        # 6. Now check-in succeeds for the approved shop
        checkin_ok = await client.post(
            "/api/v1/field/check-in",
            json={
                "shop_id": proposed_shop_id,
                "lat": 24.8620000,
                "lng": 67.0030000,
                "accuracy_meters": 4.0,
                "fix_age_seconds": 1.0,
                "is_mock": False,
            },
            headers=sp_headers,
        )
        assert checkin_ok.status_code == 200
        assert checkin_ok.json()["visit_id"] is not None


@pytest.mark.asyncio
async def test_csv_import_workflow():
    await init_db_and_seed()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"business_code": "ALNOOR", "username": "admin", "password": "admin123"},
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # 1. Test CSV Import Preview for Shops
        csv_data = """name,area_name,contact_person,contact_phone,address,city,entrance_lat,entrance_lng,entrance_pin,radius_meters
Bulk Mart 1,Saddar Market,Tariq,03001112233,Shop 1 Saddar,Karachi,24.8608,67.0012,1234,10.0
Bulk Mart 2,Gulshan-e-Iqbal,Rashid,03002223344,Block 13D,Karachi,24.9200,67.0800,4321,10.0
Bad Shop Invalid Area,NonExistentArea,NoOne,03009999999,Unknown,Karachi,24.0,67.0,0000,10.0
"""
        files = {"file": ("shops.csv", csv_data.encode("utf-8"), "text/csv")}
        preview_res = await client.post("/api/v1/shops/import/preview", files=files, headers=admin_headers)
        assert preview_res.status_code == 200, preview_res.text
        pdata = preview_res.json()
        assert pdata["valid_count"] == 2
        assert pdata["invalid_count"] == 1
        assert "NonExistentArea" in pdata["invalid_preview"][0]["errors"][0]

        # 2. Commit valid rows
        valid_items = [v["row"] for v in pdata["valid_preview"]]
        commit_res = await client.post("/api/v1/shops/import/commit", json={"valid_rows": valid_items}, headers=admin_headers)
        assert commit_res.status_code == 200
        assert commit_res.json()["imported_count"] == 2

        # Verify imported shops exist
        shops_res = await client.get("/api/v1/shops", headers=admin_headers)
        shop_names = [s["name"] for s in shops_res.json()]
        assert "Bulk Mart 1" in shop_names
        assert "Bulk Mart 2" in shop_names

