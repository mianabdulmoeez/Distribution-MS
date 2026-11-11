# Distribution Management System (DMS) — Phase 1

Production-grade multi-tenant Distribution Management System (SaaS) built specifically for Pakistani distributors.

---

## Architecture Overview

- **Backend**: FastAPI (Python) + SQLite / PostgreSQL (asyncpg/aiosqlite) + SQLAlchemy 2.0 ORM + Pydantic v2
- **Authentication**: JWT Access & Refresh tokens, Session tracking, and role-based tenant isolation
- **Field App (Android)**: Native Kotlin + Jetpack Compose + Fused Location Provider (GPS with 10m Geodesic verification)
- **Web Dashboards**: Next.js 14 + TypeScript + Tailwind CSS

---

## Key Phase 1 Features & Acceptance Criteria Verified

1. **Multi-Tenant Isolation (Acceptance Test A01)**:
   - Tenant boundaries enforced on every query.
   - Separate business codes (e.g. `ALNOOR`, `CITYSTAR`).
   - Cross-tenant data access is strictly blocked.

2. **Server-Side Location Verification (Acceptance Test A03 & Spec Section 04)**:
   - 10-meter configurable pilot radius using geodesic Haversine calculation.
   - Max horizontal accuracy threshold: $\le \min(10\text{m}, \text{shop radius})$.
   - Freshness check: GPS fix age $\le 30$ seconds.
   - Mock location signal detection & rejection.
   - Remote check-in and remote submission attempts fail with HTTP 422.

3. **Idempotency & Concurrent Retries (Acceptance Test A05)**:
   - Client generates unique UUID idempotency keys.
   - Retrying a submission returns the identical saved visit and order records without duplicate writes.
   - Payload tampering returns HTTP 409 Conflict.

4. **Complete Order & Request Lifecycles (Acceptance Test A06)**:
   - Orders: `Submitted` $\rightarrow$ `Confirmed` $\rightarrow$ `Dispatched` $\rightarrow$ `Delivered` / `Delivery Failed`.
   - Urgent custom requests captured during field visits or office entry.

5. **Reporting & Reconciliation (Acceptance Test A07)**:
   - Real-time route coverage calculation.
   - Distinct verified visit counts separated by outcome (`Order Placed`, `No Order`, `Shop Closed`, `Contact Unavailable`).
   - Field conversion rate metric and CSV export support.

---

## Local Setup & Quickstart

### 1. Backend Setup

```powershell
# Navigate to backend directory
cd F:\DMS\backend

# Install dependencies
pip install -r requirements.txt
pip install fastapi uvicorn "sqlalchemy>=2.0" aiosqlite pydantic pydantic-settings python-jose passlib bcrypt python-multipart httpx pytest pytest-asyncio greenlet pyjwt

# Seed demo database (creates Super Admin, 2 Distributor tenants, Areas, Salespeople, Shops & Products)
python app/seed.py

# Run the backend API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI Swagger documentation will be available at:
`http://localhost:8000/docs`

---

## Demo Accounts

| Role | Business Code | Username | Password |
|---|---|---|---|
| **Platform Super Admin** | *(N/A)* | `superadmin@dms.pk` | `admin123` |
| **Distributor Admin (Al-Noor)** | `ALNOOR` | `admin` | `admin123` |
| **Salesperson (Al-Noor)** | `ALNOOR` | `salesman1` | `pass123` |
| **Distributor Admin (CityStar)**| `CITYSTAR` | `admin` | `admin123` |

---

## Running the Automated Test Suite

To run all automated acceptance tests:

```powershell
pytest F:\DMS\backend\tests -v -s
```

All acceptance tests pass cleanly against the live API database!

