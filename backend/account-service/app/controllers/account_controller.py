from fastapi import Depends
from app.schemas.account_schema import LoginRequest, DeductRequest, RefundRequest
from app.services.account_service import login, get_profile, deduct, refund, get_statement
from app.middlewares.auth_middleware import get_current_user, verify_internal_token
from app.utils.response_util import success


async def login_controller(body: LoginRequest):
    return success(await login(body.username, body.password))


async def me_controller(user: dict = Depends(get_current_user)):
    return success(await get_profile(user["sub"]))


async def deduct_controller(body: DeductRequest, user: dict = Depends(get_current_user), _=Depends(verify_internal_token)):
    return success(await deduct(user["sub"], body.amount, body.transaction_id))


async def refund_controller(body: RefundRequest, user: dict = Depends(get_current_user), _=Depends(verify_internal_token)):
    return success(await refund(user["sub"], body.amount, body.transaction_id))


async def statement_controller(user: dict = Depends(get_current_user)):
    return success(await get_statement(user["sub"]))
