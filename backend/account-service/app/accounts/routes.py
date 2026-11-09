from fastapi import APIRouter, Depends
from app.core.common import success, get_current_user, verify_internal_token
from app.accounts.schemas import LoginRequest, DeductRequest, RefundRequest
from app.accounts.service import login, get_profile, deduct, refund

router = APIRouter()


@router.post("/login")
async def login_endpoint(body: LoginRequest):
    return success(await login(body.username, body.password))


@router.get("/me")
async def me_endpoint(user: dict = Depends(get_current_user)):
    return success(await get_profile(user["sub"]))


@router.post("/deduct")
async def deduct_endpoint(body: DeductRequest, _=Depends(verify_internal_token)):
    return success(await deduct(body.account_id, body.amount, body.transaction_id))


@router.post("/refund")
async def refund_endpoint(body: RefundRequest, _=Depends(verify_internal_token)):
    return success(await refund(body.account_id, body.amount, body.transaction_id))
