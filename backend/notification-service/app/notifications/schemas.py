from pydantic import BaseModel, Field


class GenerateOtpRequest(BaseModel):
    payment_id: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    student_id: str | None = None
    student_name: str | None = None
    amount: float | None = None


class VerifyOtpRequest(BaseModel):
    payment_id: str = Field(..., min_length=1)
    otp_code: str = Field(..., min_length=1)


class SendSuccessEmailRequest(BaseModel):
    email: str = Field(..., min_length=3)
    payment_id: str = Field(..., min_length=1)
    student_name: str
    student_id: str
    amount: float
    paid_at: str
