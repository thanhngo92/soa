from pydantic import BaseModel, Field


class InitiatePaymentRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    tuition_id: int | None = Field(None, description="Optional specific tuition ID to pay")


class ConfirmPaymentRequest(BaseModel):
    payment_id: str = Field(..., min_length=1)
    otp_code: str = Field(..., min_length=1)
