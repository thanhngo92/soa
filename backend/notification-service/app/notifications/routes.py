from fastapi import APIRouter, Depends
from app.core import success, verify_internal_token
from app.notifications.schemas import GenerateOtpRequest, VerifyOtpRequest, SendSuccessEmailRequest
from app.notifications.service import generate_otp, verify_otp, send_success_email

router = APIRouter()


@router.post("/otp/generate")
async def generate_otp_endpoint(body: GenerateOtpRequest, _=Depends(verify_internal_token)):
    await generate_otp(
        payment_id=body.payment_id,
        email=body.email,
        student_id=body.student_id,
        student_name=body.student_name,
        amount=body.amount,
        semester=body.semester,
    )
    return success({"status": "SENT"}, message="OTP sent")


@router.post("/otp/verify")
async def verify_otp_endpoint(body: VerifyOtpRequest, _=Depends(verify_internal_token)):
    await verify_otp(body.payment_id, body.otp_code)
    return success({"valid": True}, message="OTP verified")


@router.post("/email/success")
async def send_success_email_endpoint(body: SendSuccessEmailRequest, _=Depends(verify_internal_token)):
    await send_success_email(
        email=body.email,
        payment_id=body.payment_id,
        student_name=body.student_name,
        student_id=body.student_id,
        amount=body.amount,
        paid_at=body.paid_at,
        semester=body.semester,
    )
    return success({"status": "SENT"}, message="Email sent")
