from fastapi import Depends
from app.schemas.account_schema import LoginRequest, DeductRequest, RefundRequest
from app.services.account_service import login, get_profile, deduct, refund, get_statement
from app.middlewares.auth_middleware import get_current_user, get_optional_user, verify_internal_token
from app.utils.error_util import AppError
from app.utils.response_util import success


async def login_controller(body: LoginRequest):
    return success(await login(body.username, body.password))


async def me_controller(user: dict = Depends(get_current_user)):
    return success(await get_profile(user["sub"]))


async def deduct_controller(
    body: DeductRequest,
    user: dict | None = Depends(get_optional_user),
    _=Depends(verify_internal_token),
):
    account_id = body.account_id or (user["sub"] if user else None)
    if not account_id:
        raise AppError("UNAUTHORIZED", "Missing account_id or valid user token", 401)
    return success(await deduct(account_id, body.amount, body.transaction_id))


async def refund_controller(
    body: RefundRequest,
    user: dict | None = Depends(get_optional_user),
    _=Depends(verify_internal_token),
):
    account_id = body.account_id or (user["sub"] if user else None)
    if not account_id:
        raise AppError("UNAUTHORIZED", "Missing account_id or valid user token", 401)
    return success(await refund(account_id, body.amount, body.transaction_id))


async def statement_controller(user: dict = Depends(get_current_user)):
    return success(await get_statement(user["sub"]))
