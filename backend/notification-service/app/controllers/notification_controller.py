from fastapi import Depends
from app.schemas.notification_schema import GenerateOtpRequest, VerifyOtpRequest, SendSuccessEmailRequest
from app.services.notification_service import generate_otp, verify_otp, send_success_email
from app.middlewares.auth_middleware import verify_internal_token
from app.utils.response_util import success


async def generate_otp_controller(body: GenerateOtpRequest, _=Depends(verify_internal_token)):
    await generate_otp(
        payment_id=body.payment_id,
        email=body.email,
        student_id=body.student_id,
        student_name=body.student_name,
        amount=body.amount,
    )
    return success({"status": "SENT"}, message="OTP sent")


async def verify_otp_controller(body: VerifyOtpRequest, _=Depends(verify_internal_token)):
    await verify_otp(body.payment_id, body.otp_code)
    return success({"valid": True}, message="OTP verified")


async def send_success_email_controller(body: SendSuccessEmailRequest, _=Depends(verify_internal_token)):
    await send_success_email(body.email, body.payment_id, body.student_name, body.student_id, body.amount, body.paid_at)
    return success({"status": "SENT"}, message="Email sent")
