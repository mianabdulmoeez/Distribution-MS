from fastapi import APIRouter

from app.api.v1 import (
    auth,
    businesses,
    field,
    orders,
    plans,
    platform,
    products,
    reports,
    shops,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(platform.router)
api_router.include_router(businesses.router)
api_router.include_router(shops.router)
api_router.include_router(plans.router)
api_router.include_router(field.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(reports.router)

