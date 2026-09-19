from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class DeductRequest(BaseModel):
    amount: float = Field(..., gt=0)
    transaction_id: str


class RefundRequest(BaseModel):
    amount: float = Field(..., gt=0)
    transaction_id: str
