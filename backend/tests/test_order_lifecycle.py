import sys
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append("F:\\DMS\\backend")

from app.main import app


@pytest.mark.asyncio
async def test_order_and_urgent_request_lifecycle():
    from app.seed import init_db_and_seed
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

        # 2. Get assigned shop (Bismillah General Store, entrance_lat: 24.8607, entrance_lng: 67.0011)
        shops_res = await client.get("/api/v1/field/shops", headers=sp_headers)
        assert shops_res.status_code == 200
        shops = shops_res.json()
        bismillah_shop = next(s for s in shops if s["name"] == "Bismillah General Store")
        shop_id = bismillah_shop["id"]

        # 3. Check in at shop location
        checkin_res = await client.post(
            "/api/v1/field/check-in",
            json={
                "shop_id": shop_id,
                "lat": 24.8607000,
                "lng": 67.0011000,
                "accuracy_meters": 4.0,
                "fix_age_seconds": 1.0,
                "is_mock": False,
            },
            headers=sp_headers,
        )
        assert checkin_res.status_code == 200
        v_data = checkin_res.json()
        visit_id = v_data["visit_id"]
        grant_id = v_data["grant_id"]

        # 4. Get active products
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"business_code": "ALNOOR", "username": "admin", "password": "admin123"},
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        prods_res = await client.get("/api/v1/products", headers=admin_headers)
        assert prods_res.status_code == 200
        prods = prods_res.json()
        tea_prod = next(p for p in prods if "Tea" in p["name"])

        # 5. Submit field visit with both an order and an urgent custom request
        submit_res = await client.post(
            "/api/v1/field/submit",
            json={
                "visit_id": visit_id,
                "grant_id": grant_id,
                "outcome": "order_placed",
                "notes": "Urgent stock required before evening",
                "lat": 24.8607010,
                "lng": 67.0011010,
                "accuracy_meters": 3.5,
                "fix_age_seconds": 1.0,
                "is_mock": False,
                "idempotency_key": "order-submit-test-key-01",
                "order_lines": [{"product_id": tea_prod["id"], "qty_requested": 5}],
                "custom_request": {
                    "item_description": "Special branded promotional tea mugs (12 pcs)",
                    "priority": "urgent",
                    "callback_phone": "+923121112233",
                },
            },
            headers=sp_headers,
        )
        assert submit_res.status_code == 200, submit_res.text
        sub_data = submit_res.json()
        order_id = sub_data["order_id"]
        assert order_id is not None
        assert sub_data["custom_request_id"] is not None

        # 6. Admin inspects order lifecycle: Submitted -> Confirmed -> Dispatched -> Delivered
        ord_res = await client.get(f"/api/v1/orders/{order_id}", headers=admin_headers)
        assert ord_res.status_code == 200
        ord_data = ord_res.json()
        assert ord_data["status"] == "submitted"
        assert ord_data["total_amount"] == 3250.0  # 5 * 650

        # Confirm
        conf_res = await client.post(f"/api/v1/orders/{order_id}/confirm", json={"notes": "Approved by manager"}, headers=admin_headers)
        assert conf_res.status_code == 200
        assert conf_res.json()["status"] == "confirmed"

        # Dispatch
        disp_res = await client.post(f"/api/v1/orders/{order_id}/dispatch", json={"dispatch_reference": "DISP-2026-001"}, headers=admin_headers)
        assert disp_res.status_code == 200
        assert disp_res.json()["status"] == "dispatched"

        # Deliver
        deliv_res = await client.post(f"/api/v1/orders/{order_id}/deliver", json={"recipient": "Haji Rasheed"}, headers=admin_headers)
        assert deliv_res.status_code == 200
        assert deliv_res.json()["status"] == "delivered"

        print("\n============================================================")
        print("ORDER & URGENT REQUEST LIFECYCLE ACCEPTANCE TESTS PASSED!")
        print("============================================================")
