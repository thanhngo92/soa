from pydantic import BaseModel, Field


class InitiatePaymentRequest(BaseModel):
    student_id: str = Field(..., min_length=1)


class ConfirmPaymentRequest(BaseModel):
    payment_id: str = Field(..., min_length=1)
    otp_code: str = Field(..., min_length=1)
