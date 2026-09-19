from pydantic import BaseModel
from typing import Optional


class InitiatePaymentRequest(BaseModel):
    student_id: str


class ConfirmPaymentRequest(BaseModel):
    payment_id: str
    otp_code: str
