from fastapi import APIRouter
from app.routes.notification_routes import router as notification_router

router = APIRouter()
router.include_router(notification_router)
