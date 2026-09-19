from fastapi import Depends
from app.schemas.account_schema import LoginRequest, DeductRequest, RefundRequest
from app.services.account_service import login, get_profile, deduct, refund
from app.middlewares.auth_middleware import get_current_user
from app.utils.response_util import success


async def login_controller(body: LoginRequest):
    return success(await login(body.username, body.password))


async def me_controller(user: dict = Depends(get_current_user)):
    return success(await get_profile(user["sub"]))


async def deduct_controller(body: DeductRequest, user: dict = Depends(get_current_user)):
    return success(await deduct(user["sub"], body.amount))


async def refund_controller(body: RefundRequest, user: dict = Depends(get_current_user)):
    return success(await refund(user["sub"], body.amount))
