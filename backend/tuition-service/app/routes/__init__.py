from fastapi import APIRouter
from app.routes.tuition_routes import router as tuition_router

router = APIRouter()
router.include_router(tuition_router)
