import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import CurrentMembership, CurrentUser, DBSession
from app.models.catalog import CustomRequest, Order, OrderLine, Product
from app.models.operations import AuditEvent, IdempotencyRecord
from app.models.territory import (
    AreaAssignment,
    PlannedStop,
    PlannedStopStatus,
    Shop,
    ShopProposal,
    ShopStatus,
)
from app.models.user import MembershipRole
from app.models.visit import (
    ChallengeType,
    CheckAttempt,
    CheckResult,
    LocationChallenge,
    Visit,
    VisitGrant,
    VisitOutcome,
)
from app.schemas.visit import (
    CheckInRequest,
    CheckInResponse,
    VisitSubmitRequest,
    VisitSubmitResponse,
)
from app.services.location import verify_location

router = APIRouter(prefix="/field", tags=["Salesperson Field Operations"])


def require_salesperson(membership: CurrentMembership):
    if membership.role != MembershipRole.salesperson:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Salesperson role required",
        )
    return membership


@router.get("/today")
async def get_today_stops(
    sp: Annotated[CurrentMembership, Depends(require_salesperson)],
    db: DBSession,
):
    today = datetime.now(timezone.utc).date()
    stmt = (
        select(PlannedStop, Shop)
        .join(Shop, PlannedStop.shop_id == Shop.id)
        .where(
            PlannedStop.tenant_id == sp.tenant_id,
            PlannedStop.membership_id == sp.id,
            PlannedStop.service_date == today,
        )
        .order_by(PlannedStop.sequence_order)
    )
    res = await db.execute(stmt)
    rows = res.all()
    return [
        {
            "stop_id": str(stop.id),
            "sequence_order": stop.sequence_order,
            "status": stop.status.value,
            "shop": {
                "id": str(shop.id),
                "name": shop.name,
                "address": shop.address,
                "city": shop.city,
                "entrance_lat": float(shop.entrance_lat),
                "entrance_lng": float(shop.entrance_lng),
                "entrance_pin": shop.entrance_pin,
                "radius_meters": shop.radius_meters,
            },
        }
        for stop, shop in rows
    ]


@router.get("/shops")
async def get_assigned_shops(
    sp: Annotated[CurrentMembership, Depends(require_salesperson)],
    db: DBSession,
):
    # Find all active area assignments for this salesperson
    asgn_stmt = select(AreaAssignment.area_id).where(
        AreaAssignment.tenant_id == sp.tenant_id,
        AreaAssignment.membership_id == sp.id,
        AreaAssignment.is_active.is_(True),
    )
    asgn_res = await db.execute(asgn_stmt)
    assigned_area_ids = asgn_res.scalars().all()

    if not assigned_area_ids:
        return []

    # Get approved shops in these areas
    shop_stmt = (
        select(Shop)
        .where(
            Shop.tenant_id == sp.tenant_id,
            Shop.area_id.in_(assigned_area_ids),
            Shop.status == ShopStatus.approved,
        )
        .order_by(Shop.name)
    )
    shop_res = await db.execute(shop_stmt)
    shops = shop_res.scalars().all()

    return [
        {
            "id": str(s.id),
            "name": s.name,
            "area_id": str(s.area_id),
            "address": s.address,
            "landmark": s.landmark,
            "city": s.city,
            "contact_person": s.contact_person,
            "contact_phone": s.contact_phone,
            "entrance_lat": float(s.entrance_lat),
            "entrance_lng": float(s.entrance_lng),
            "entrance_pin": s.entrance_pin,
            "radius_meters": s.radius_meters,
        }
        for s in shops
    ]


class ShopProposalRequest(BaseModel):
    area_id: uuid.UUID
    name: str
    contact_person: str | None = None
    contact_phone: str | None = None
    address: str
    landmark: str | None = None
    city: str
    entrance_lat: float
    entrance_lng: float
    accuracy_meters: float
    entrance_pin: str
    photo_url: str | None = None


@router.post("/shops/propose")
async def propose_shop(
    req: ShopProposalRequest,
    sp: Annotated[CurrentMembership, Depends(require_salesperson)],
    db: DBSession,
):
    """
    Spec Section 03 & Acceptance Test A02:
    Propose a shop in an assigned area.
    Captures fresh location, accuracy and proposer identity.
    A field-proposed shop stays unavailable for orders until approved.
    """
    # Verify salesperson is assigned to this area
    asgn_res = await db.execute(
        select(AreaAssignment).where(
            AreaAssignment.tenant_id == sp.tenant_id,
            AreaAssignment.membership_id == sp.id,
            AreaAssignment.area_id == req.area_id,
            AreaAssignment.is_active.is_(True),
        )
    )
    if not asgn_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this area",
        )

    # Create Pending Shop record so it has an ID, but status is pending
    shop = Shop(
        tenant_id=sp.tenant_id,
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
        radius_meters=10.0,
        status=ShopStatus.pending,
        pin_version=1,
    )
    db.add(shop)
    await db.flush()

    proposal = ShopProposal(
        tenant_id=sp.tenant_id,
        shop_id=shop.id,
        proposed_by=sp.id,
        name=req.name,
        contact_person=req.contact_person,
        contact_phone=req.contact_phone,
        address=req.address,
        landmark=req.landmark,
        city=req.city,
        area_id=req.area_id,
        lat=req.entrance_lat,
        lng=req.entrance_lng,
        accuracy_meters=req.accuracy_meters,
        entrance_pin=req.entrance_pin,
        photo_url=req.photo_url,
        status="pending",
    )
    db.add(proposal)
    await db.commit()

    return {
        "shop_id": str(shop.id),
        "proposal_id": str(proposal.id),
        "name": shop.name,
        "status": shop.status.value,
        "message": "Shop proposed successfully. Awaiting business admin review and approval.",
    }


@router.post("/check-in", response_model=CheckInResponse)
async def check_in(
    req: CheckInRequest,
    sp: Annotated[CurrentMembership, Depends(require_salesperson)],
    current_user: CurrentUser,
    db: DBSession,
):
    # 1. Resolve shop and verify it is approved & in tenant
    shop_res = await db.execute(
        select(Shop).where(Shop.id == req.shop_id, Shop.tenant_id == sp.tenant_id)
    )
    shop = shop_res.scalar_one_or_none()
    if not shop or shop.status != ShopStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop is not approved or not found",
        )

    # 2. Verify salesperson has active area assignment covering the shop's area
    asgn_res = await db.execute(
        select(AreaAssignment).where(
            AreaAssignment.tenant_id == sp.tenant_id,
            AreaAssignment.membership_id == sp.id,
            AreaAssignment.area_id == shop.area_id,
            AreaAssignment.is_active.is_(True),
        )
    )
    if not asgn_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this shop's area",
        )

    # 3. Create challenge token
    challenge_token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    challenge = LocationChallenge(
        tenant_id=sp.tenant_id,
        membership_id=sp.id,
        session_id=None,
        shop_id=shop.id,
        challenge_token=challenge_token,
        challenge_type=ChallengeType.check_in,
        expires_at=now + timedelta(seconds=settings.CHALLENGE_EXPIRY_SECONDS),
    )
    db.add(challenge)
    await db.flush()

    # 4. Perform server-side location verification
    accepted, reason_code, distance = verify_location(
        fix_lat=req.lat,
        fix_lng=req.lng,
        shop_lat=float(shop.entrance_lat),
        shop_lng=float(shop.entrance_lng),
        accuracy_meters=req.accuracy_meters,
        fix_age_seconds=req.fix_age_seconds,
        is_mock=req.is_mock,
        radius_meters=shop.radius_meters,
        max_accuracy=settings.MAX_ACCURACY_METERS,
        max_fix_age=settings.MAX_FIX_AGE_SECONDS,
    )

    # Record CheckAttempt regardless of outcome
    attempt = CheckAttempt(
        tenant_id=sp.tenant_id,
        membership_id=sp.id,
        shop_id=shop.id,
        challenge_id=challenge.id,
        lat=req.lat,
        lng=req.lng,
        accuracy_meters=req.accuracy_meters,
        fix_age_seconds=req.fix_age_seconds,
        is_mock=req.is_mock,
        distance_meters=distance,
        result=CheckResult(accepted and "accepted" or reason_code),
        reason_code=reason_code if not accepted else None,
        radius_used=shop.radius_meters,
    )
    db.add(attempt)

    if not accepted:
        await db.commit()
        error_messages = {
            "rejected_distance": f"Out of radius: you are {distance:.1f}m away (maximum {shop.radius_meters}m allowed). Move closer to the entrance pin.",
            "rejected_accuracy": f"Location accuracy too low: {req.accuracy_meters:.1f}m reported (maximum {min(settings.MAX_ACCURACY_METERS, shop.radius_meters)}m required).",
            "rejected_stale": f"GPS fix is stale: {req.fix_age_seconds:.1f}s old (maximum {settings.MAX_FIX_AGE_SECONDS}s allowed).",
            "rejected_mock": "Mock location detected. Please disable simulated or mock locations.",
        }
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_messages.get(reason_code, f"Location verification failed: {reason_code}"),
        )

    # 5. Check if linked to today's planned stop
    today = now.date()
    stop_res = await db.execute(
        select(PlannedStop).where(
            PlannedStop.tenant_id == sp.tenant_id,
            PlannedStop.membership_id == sp.id,
            PlannedStop.shop_id == shop.id,
            PlannedStop.service_date == today,
            PlannedStop.status == PlannedStopStatus.scheduled,
        )
    )
    planned_stop = stop_res.scalar_one_or_none()

    # 6. Create Visit record (open state)
    visit = Visit(
        tenant_id=sp.tenant_id,
        membership_id=sp.id,
        shop_id=shop.id,
        planned_stop_id=planned_stop.id if planned_stop else None,
        outcome=VisitOutcome.no_order,  # Default, updated on submit
        check_in_at=now,
        is_verified=True,
        is_ad_hoc=(planned_stop is None),
    )
    db.add(visit)
    await db.flush()

    # 7. Issue 15-minute VisitGrant
    grant_expires_at = now + timedelta(minutes=settings.VISIT_GRANT_LIFETIME_MINUTES)
    grant = VisitGrant(
        tenant_id=sp.tenant_id,
        membership_id=sp.id,
        session_id=None,
        shop_id=shop.id,
        visit_id=visit.id,
        pin_version=shop.pin_version,
        check_challenge_id=challenge.id,
        is_active=True,
        expires_at=grant_expires_at,
    )
    db.add(grant)
    await db.commit()

    return CheckInResponse(
        visit_id=visit.id,
        grant_id=grant.id,
        challenge_token=challenge_token,
        grant_expires_at=grant_expires_at,
        distance_meters=round(distance, 1),
    )


@router.post("/submit", response_model=VisitSubmitResponse)
async def submit_visit_outcome(
    req: VisitSubmitRequest,
    sp: Annotated[CurrentMembership, Depends(require_salesperson)],
    current_user: CurrentUser,
    db: DBSession,
):
    now = datetime.now(timezone.utc)

    # 1. Idempotency Check
    idem_res = await db.execute(
        select(IdempotencyRecord).where(
            IdempotencyRecord.tenant_id == sp.tenant_id,
            IdempotencyRecord.actor_id == current_user.id,
            IdempotencyRecord.operation == "visit_submit",
            IdempotencyRecord.idempotency_key == req.idempotency_key,
        )
    )
    existing_record = idem_res.scalar_one_or_none()
    if existing_record:
        # Return identical saved result if payload matches, or 409 conflict
        payload_dict = req.model_dump(exclude={"idempotency_key"}, mode="json")
        payload_hash = str(hash(json.dumps(payload_dict, sort_keys=True)))
        if existing_record.request_hash != payload_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key reused with conflicting payload",
            )
        resp_data = existing_record.response_data
        return VisitSubmitResponse(**resp_data)

    # 2. Verify grant is valid, active, and not expired
    grant_res = await db.execute(
        select(VisitGrant).where(
            VisitGrant.id == req.grant_id,
            VisitGrant.tenant_id == sp.tenant_id,
            VisitGrant.membership_id == sp.id,
            VisitGrant.visit_id == req.visit_id,
            VisitGrant.is_active.is_(True),
        )
    )
    grant = grant_res.scalar_one_or_none()
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Visit grant has expired or is invalid. Please check in again.",
        )
    grant_exp = grant.expires_at
    if grant_exp.tzinfo is None:
        grant_exp = grant_exp.replace(tzinfo=timezone.utc)
    if grant_exp < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Visit grant has expired or is invalid. Please check in again.",
        )

    # 3. Resolve visit and shop
    visit_res = await db.execute(
        select(Visit).where(Visit.id == req.visit_id, Visit.tenant_id == sp.tenant_id)
    )
    visit = visit_res.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    shop_res = await db.execute(
        select(Shop).where(Shop.id == visit.shop_id, Shop.tenant_id == sp.tenant_id)
    )
    shop = shop_res.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    # 4. Mandatory fresh server-side location verification at submission time
    accepted, reason_code, distance = verify_location(
        fix_lat=req.lat,
        fix_lng=req.lng,
        shop_lat=float(shop.entrance_lat),
        shop_lng=float(shop.entrance_lng),
        accuracy_meters=req.accuracy_meters,
        fix_age_seconds=req.fix_age_seconds,
        is_mock=req.is_mock,
        radius_meters=shop.radius_meters,
        max_accuracy=settings.MAX_ACCURACY_METERS,
        max_fix_age=settings.MAX_FIX_AGE_SECONDS,
    )

    if not accepted:
        error_messages = {
            "rejected_distance": f"Submission out of radius: you are {distance:.1f}m away (maximum {shop.radius_meters}m).",
            "rejected_accuracy": f"Location accuracy too low: {req.accuracy_meters:.1f}m reported.",
            "rejected_stale": f"GPS fix is stale: {req.fix_age_seconds:.1f}s old.",
            "rejected_mock": "Mock location detected at submission.",
        }
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_messages.get(reason_code, f"Submission location verification failed: {reason_code}"),
        )

    # 5. In ONE atomic transaction:
    # Update Visit
    outcome_enum = VisitOutcome(req.outcome)
    visit.outcome = outcome_enum
    visit.no_order_reason = req.no_order_reason
    visit.notes = req.notes
    visit.submit_lat = req.lat
    visit.submit_lng = req.lng
    visit.submit_accuracy = req.accuracy_meters
    visit.submit_distance = distance
    visit.submitted_at = now
    visit.idempotency_key = req.idempotency_key

    # Deactivate grant so it cannot be reused
    grant.is_active = False

    order_id = None
    # If order lines placed, create Order + OrderLines
    if req.order_lines:
        order = Order(
            tenant_id=sp.tenant_id,
            shop_id=shop.id,
            visit_id=visit.id,
            membership_id=sp.id,
            created_by=current_user.id,
            origin="field",
            status="submitted",
            total_amount=0,
            is_urgent=False,
            notes=req.notes,
        )
        db.add(order)
        await db.flush()

        total = 0
        for line_input in req.order_lines:
            p_res = await db.execute(
                select(Product).where(
                    Product.id == line_input.product_id, Product.tenant_id == sp.tenant_id
                )
            )
            prod = p_res.scalar_one_or_none()
            if not prod:
                raise HTTPException(status_code=400, detail="Product not found")

            ltotal = prod.price_pkr * line_input.qty_requested
            total += ltotal
            oline = OrderLine(
                order_id=order.id,
                tenant_id=sp.tenant_id,
                product_id=prod.id,
                product_name=prod.name,
                product_sku=prod.sku,
                unit=prod.unit,
                unit_price=prod.price_pkr,
                qty_requested=line_input.qty_requested,
                line_total=ltotal,
            )
            db.add(oline)

        order.total_amount = total
        order_id = order.id

    # If custom request, create CustomRequest
    custom_req_id = None
    if req.custom_request:
        creq = CustomRequest(
            tenant_id=sp.tenant_id,
            shop_id=shop.id,
            visit_id=visit.id,
            membership_id=sp.id,
            created_by=current_user.id,
            item_description=req.custom_request.item_description,
            quantity=req.custom_request.quantity,
            requirements=req.custom_request.requirements,
            priority=req.custom_request.priority,
            requested_by_time=req.custom_request.requested_by_time,
            callback_phone=req.custom_request.callback_phone,
            callback_note=req.custom_request.callback_note,
            status="new",
            origin="field",
            reference_id=f"REQ-{uuid.uuid4().hex[:8].upper()}",
        )
        db.add(creq)
        await db.flush()
        custom_req_id = creq.id

    # Update planned stop if exists
    if visit.planned_stop_id:
        p_stop_res = await db.execute(
            select(PlannedStop).where(PlannedStop.id == visit.planned_stop_id)
        )
        p_stop = p_stop_res.scalar_one_or_none()
        if p_stop:
            p_stop.status = PlannedStopStatus.completed
            p_stop.visit_id = visit.id

    # Record Audit Event
    audit = AuditEvent(
        tenant_id=sp.tenant_id,
        actor_id=current_user.id,
        action="visit_submitted",
        record_type="visit",
        record_id=visit.id,
        reason=f"Outcome: {req.outcome}",
    )
    db.add(audit)

    # Save Idempotency Record
    payload_dict = req.model_dump(exclude={"idempotency_key"}, mode="json")
    payload_hash = str(hash(json.dumps(payload_dict, sort_keys=True)))
    response_payload = {
        "visit": {
            "id": str(visit.id),
            "tenant_id": str(visit.tenant_id),
            "membership_id": str(visit.membership_id),
            "shop_id": str(visit.shop_id),
            "planned_stop_id": str(visit.planned_stop_id) if visit.planned_stop_id else None,
            "outcome": visit.outcome.value,
            "no_order_reason": visit.no_order_reason,
            "notes": visit.notes,
            "check_in_at": visit.check_in_at.isoformat(),
            "submitted_at": visit.submitted_at.isoformat(),
            "submit_distance": visit.submit_distance,
            "is_verified": visit.is_verified,
            "is_ad_hoc": visit.is_ad_hoc,
            "created_at": visit.created_at.isoformat(),
        },
        "order_id": str(order_id) if order_id else None,
        "custom_request_id": str(custom_req_id) if custom_req_id else None,
        "message": "Visit outcome submitted successfully",
    }
    idem_rec = IdempotencyRecord(
        tenant_id=sp.tenant_id,
        actor_id=current_user.id,
        operation="visit_submit",
        idempotency_key=req.idempotency_key,
        request_hash=payload_hash,
        response_data=response_payload,
        expires_at=now + timedelta(days=7),
    )
    db.add(idem_rec)

    await db.commit()

    return VisitSubmitResponse(
        visit=visit,
        order_id=order_id,
        custom_request_id=custom_req_id,
    )


@router.get("/my-activity")
async def get_my_activity(
    sp: Annotated[CurrentMembership, Depends(require_salesperson)],
    db: DBSession,
):
    stmt = (
        select(Visit, Shop)
        .join(Shop, Visit.shop_id == Shop.id)
        .where(Visit.tenant_id == sp.tenant_id, Visit.membership_id == sp.id)
        .order_by(Visit.created_at.desc())
        .limit(50)
    )
    res = await db.execute(stmt)
    rows = res.all()
    return [
        {
            "visit_id": str(v.id),
            "shop_name": s.name,
            "address": s.address,
            "outcome": v.outcome.value,
            "no_order_reason": v.no_order_reason,
            "check_in_at": v.check_in_at,
            "submitted_at": v.submitted_at,
            "distance_meters": v.submit_distance,
            "is_verified": v.is_verified,
        }
        for v, s in rows
    ]
