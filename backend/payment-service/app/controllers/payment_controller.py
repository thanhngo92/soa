from fastapi import Depends, Request
from app.schemas.payment_schema import InitiatePaymentRequest, ConfirmPaymentRequest
from app.services.payment_service import initiate, confirm, history
from app.middlewares.auth_middleware import get_current_user
from app.utils.response_util import success


async def initiate_controller(body: InitiatePaymentRequest, request: Request, user: dict = Depends(get_current_user)):
    return success(await initiate(request, user, body.student_id))


async def confirm_controller(body: ConfirmPaymentRequest, request: Request, user: dict = Depends(get_current_user)):
    return success(await confirm(request, user, body.payment_id, body.otp_code))


async def history_controller(user: dict = Depends(get_current_user)):
    return success(await history(user["sub"]))
