import csv
import io
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentMembership, DBSession
from app.models.catalog import Order, OrderStatus
from app.models.territory import PlannedStop, PlannedStopStatus, Shop
from app.models.user import Membership, MembershipRole, User
from app.models.visit import Visit, VisitOutcome

router = APIRouter(prefix="/reports", tags=["Distributor Reports and Summaries"])


def require_business_admin(membership: CurrentMembership):
    if membership.role != MembershipRole.business_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business admin role required",
        )
    return membership


@router.get("/dashboard")
async def get_dashboard_summary(
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
):
    today = datetime.now(timezone.utc).date()

    # 1. Today's stops
    stops_res = await db.execute(
        select(PlannedStop).where(
            PlannedStop.tenant_id == admin.tenant_id,
            PlannedStop.service_date == today,
        )
    )
    stops = stops_res.scalars().all()
    total_stops = len(stops)
    completed_stops = sum(1 for s in stops if s.status == PlannedStopStatus.completed)

    # 2. Orders awaiting action
    pending_orders_res = await db.execute(
        select(func.count(Order.id)).where(
            Order.tenant_id == admin.tenant_id,
            Order.status == OrderStatus.submitted,
        )
    )
    pending_orders = pending_orders_res.scalar() or 0

    # 3. Verified visits today
    today_dt_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    visits_res = await db.execute(
        select(Visit).where(
            Visit.tenant_id == admin.tenant_id,
            Visit.created_at >= today_dt_start,
            Visit.is_verified.is_(True),
        )
    )
    visits = visits_res.scalars().all()
    verified_visits_count = len(visits)
    no_order_count = sum(1 for v in visits if v.outcome == VisitOutcome.no_order)
    order_placed_count = sum(1 for v in visits if v.outcome == VisitOutcome.order_placed)

    return {
        "service_date": str(today),
        "planned_coverage": {
            "total_stops": total_stops,
            "completed_stops": completed_stops,
            "coverage_percentage": (completed_stops / total_stops * 100.0) if total_stops > 0 else 0.0,
        },
        "visits": {
            "total_verified": verified_visits_count,
            "order_placed": order_placed_count,
            "no_order": no_order_count,
            "other_outcomes": verified_visits_count - order_placed_count - no_order_count,
        },
        "orders_pending_confirmation": pending_orders,
    }


@router.get("/weekly-summary")
async def get_weekly_summary(
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
    start_date: date | None = None,
    end_date: date | None = None,
):
    today = datetime.now(timezone.utc).date()
    # Default: Monday through Sunday of current week
    if not start_date:
        start_date = today - timedelta(days=today.weekday())
    if not end_date:
        end_date = start_date + timedelta(days=6)

    dt_start = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    dt_end = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    # 1. Planned stops count
    stops_res = await db.execute(
        select(PlannedStop).where(
            PlannedStop.tenant_id == admin.tenant_id,
            PlannedStop.service_date >= start_date,
            PlannedStop.service_date <= end_date,
            PlannedStop.status != PlannedStopStatus.cancelled,
        )
    )
    all_stops = stops_res.scalars().all()
    total_assigned_stops = len(all_stops)
    verified_completed_stops = sum(1 for s in all_stops if s.status == PlannedStopStatus.completed)
    planned_coverage_pct = (
        round(verified_completed_stops / total_assigned_stops * 100, 1)
        if total_assigned_stops > 0
        else None
    )

    # 2. Distinct verified visits
    visits_res = await db.execute(
        select(Visit).where(
            Visit.tenant_id == admin.tenant_id,
            Visit.created_at >= dt_start,
            Visit.created_at <= dt_end,
            Visit.is_verified.is_(True),
        )
    )
    visits = visits_res.scalars().all()
    distinct_verified_visits = len(visits)

    no_order_count = sum(1 for v in visits if v.outcome == VisitOutcome.no_order)
    closed_count = sum(1 for v in visits if v.outcome == VisitOutcome.shop_closed)
    unavailable_count = sum(1 for v in visits if v.outcome == VisitOutcome.contact_unavailable)
    custom_request_count = sum(1 for v in visits if v.outcome == VisitOutcome.custom_request_only)
    order_placed_count = sum(1 for v in visits if v.outcome == VisitOutcome.order_placed)

    # 3. Field conversion
    field_conversion_pct = (
        round(order_placed_count / distinct_verified_visits * 100, 1)
        if distinct_verified_visits > 0
        else None
    )

    # 4. Orders
    orders_res = await db.execute(
        select(Order).where(
            Order.tenant_id == admin.tenant_id,
            Order.created_at >= dt_start,
            Order.created_at <= dt_end,
        )
    )
    orders = orders_res.scalars().all()
    field_orders = [o for o in orders if o.origin.value == "field"]
    office_orders = [o for o in orders if o.origin.value == "office"]

    total_submitted_val = sum(float(o.total_amount) for o in orders)
    delivered_val = sum(
        float(o.confirmed_amount or o.total_amount)
        for o in orders
        if o.status == OrderStatus.delivered
    )

    return {
        "period": {
            "start_date": str(start_date),
            "end_date": str(end_date),
            "timezone": "Asia/Karachi",
        },
        "metrics": {
            "total_assigned_stops": total_assigned_stops,
            "verified_completed_stops": verified_completed_stops,
            "planned_coverage_pct": planned_coverage_pct,
            "distinct_verified_visits": distinct_verified_visits,
            "outcome_breakdown": {
                "order_placed": order_placed_count,
                "no_order": no_order_count,
                "shop_closed": closed_count,
                "contact_unavailable": unavailable_count,
                "custom_request_only": custom_request_count,
            },
            "field_conversion_pct": field_conversion_pct,
            "order_totals": {
                "total_field_orders": len(field_orders),
                "total_office_orders": len(office_orders),
                "submitted_value_pkr": total_submitted_val,
                "delivered_value_pkr": delivered_val,
            },
        },
    }


@router.get("/export/csv")
async def export_weekly_summary_csv(
    admin: Annotated[CurrentMembership, Depends(require_business_admin)],
    db: DBSession,
    start_date: date | None = None,
    end_date: date | None = None,
):
    summary = await get_weekly_summary(admin, db, start_date, end_date)
    m = summary["metrics"]
    ob = m["outcome_breakdown"]
    ot = m["order_totals"]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Distribution Management System - Weekly Salesperson Summary"])
    writer.writerow(["Period Start", summary["period"]["start_date"]])
    writer.writerow(["Period End", summary["period"]["end_date"]])
    writer.writerow(["Timezone", summary["period"]["timezone"]])
    writer.writerow([])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Assigned Stops", m["total_assigned_stops"]])
    writer.writerow(["Verified Completed Stops", m["verified_completed_stops"]])
    writer.writerow(["Planned Coverage %", m["planned_coverage_pct"] or ""])
    writer.writerow(["Distinct Verified Visits", m["distinct_verified_visits"]])
    writer.writerow(["- Order Placed Visits", ob["order_placed"]])
    writer.writerow(["- No Order Visits", ob["no_order"]])
    writer.writerow(["- Shop Closed Visits", ob["shop_closed"]])
    writer.writerow(["- Contact Unavailable Visits", ob["contact_unavailable"]])
    writer.writerow(["- Custom Request Only", ob["custom_request_only"]])
    writer.writerow(["Field Conversion %", m["field_conversion_pct"] or ""])
    writer.writerow(["Field Orders Count", ot["total_field_orders"]])
    writer.writerow(["Office Orders Count", ot["total_office_orders"]])
    writer.writerow(["Total Submitted Value (PKR)", ot["submitted_value_pkr"]])
    writer.writerow(["Delivered Value (PKR)", ot["delivered_value_pkr"]])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=weekly_summary_{summary['period']['start_date']}.csv"},
    )

