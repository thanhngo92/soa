from fastapi import Depends
from app.schemas.notification_schema import GenerateOtpRequest, VerifyOtpRequest, SendSuccessEmailRequest
from app.services.notification_service import generate_otp, verify_otp, send_success_email
from app.middlewares.auth_middleware import verify_internal_token
from app.utils.response_util import success


async def generate_otp_controller(body: GenerateOtpRequest, _=Depends(verify_internal_token)):
    await generate_otp(body.payment_id, body.email)
    return success(message="OTP sent")


async def verify_otp_controller(body: VerifyOtpRequest, _=Depends(verify_internal_token)):
    await verify_otp(body.payment_id, body.otp_code)
    return success(message="OTP verified")


async def send_success_email_controller(body: SendSuccessEmailRequest, _=Depends(verify_internal_token)):
    await send_success_email(body.email, body.payment_id, body.student_name, body.student_id, body.amount, body.paid_at)
    return success(message="Email sent")
