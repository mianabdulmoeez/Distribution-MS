import math


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate geodesic distance in meters using Haversine formula.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def verify_location(
    fix_lat: float,
    fix_lng: float,
    shop_lat: float,
    shop_lng: float,
    accuracy_meters: float,
    fix_age_seconds: float,
    is_mock: bool = False,
    radius_meters: float = 10.0,
    max_accuracy: float = 10.0,
    max_fix_age: float = 30.0,
) -> tuple[bool, str, float]:
    """
    Verifies location per Phase 1 Spec Section 04:
    - Reported accuracy must be <= min(10m, shop radius)
    - Fix age must be <= 30 seconds
    - Mock signals must not be set
    - Geodesic distance must be <= radius_meters

    Returns (accepted: bool, reason_code: str, distance_meters: float)
    """
    dist = haversine_distance(fix_lat, fix_lng, shop_lat, shop_lng)

    if is_mock:
        return False, "rejected_mock", dist

    if fix_age_seconds > max_fix_age:
        return False, "rejected_stale", dist

    allowed_accuracy = min(max_accuracy, radius_meters)
    if accuracy_meters > allowed_accuracy:
        return False, "rejected_accuracy", dist

    if dist > radius_meters:
        return False, "rejected_distance", dist

    return True, "accepted", dist

