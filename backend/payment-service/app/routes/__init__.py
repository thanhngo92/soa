from fastapi import APIRouter
from app.routes.payment_routes import router as payment_router

router = APIRouter()
router.include_router(payment_router)
