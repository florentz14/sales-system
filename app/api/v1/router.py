from fastapi import APIRouter

from app.api.v1 import auth, customers, invoices, products, reports, users

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router, prefix="/auth")
api_v1_router.include_router(products.router)
api_v1_router.include_router(customers.router)
api_v1_router.include_router(invoices.router)
api_v1_router.include_router(reports.router)
api_v1_router.include_router(users.router)
