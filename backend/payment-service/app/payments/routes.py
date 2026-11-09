from fastapi import APIRouter, Depends, Request
from app.core import success, get_current_user
from app.payments.schemas import InitiatePaymentRequest, ConfirmPaymentRequest
from app.payments.service import initiate, confirm, history

router = APIRouter()


@router.post("/initiate")
async def initiate_endpoint(body: InitiatePaymentRequest, request: Request, user: dict = Depends(get_current_user)):
    return success(await initiate(request, user, body.student_id))


@router.post("/confirm")
async def confirm_endpoint(body: ConfirmPaymentRequest, request: Request, user: dict = Depends(get_current_user)):
    return success(await confirm(request, user, body.payment_id, body.otp_code))


@router.get("/history")
async def history_endpoint(request: Request, user: dict = Depends(get_current_user)):
    return success(await history(request, user["sub"]))
