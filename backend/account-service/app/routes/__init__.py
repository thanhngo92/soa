from fastapi import APIRouter
from app.routes.account_routes import router as account_router

router = APIRouter()
router.include_router(account_router)
