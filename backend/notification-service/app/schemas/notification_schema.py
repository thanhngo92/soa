from pydantic import BaseModel


class GenerateOtpRequest(BaseModel):
    payment_id: str
    email: str


class VerifyOtpRequest(BaseModel):
    payment_id: str
    otp_code: str


class SendSuccessEmailRequest(BaseModel):
    email: str
    payment_id: str
    student_name: str
    student_id: str
    amount: float
    paid_at: str
