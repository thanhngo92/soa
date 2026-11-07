from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class DeductRequest(BaseModel):
    account_id: str | None = None
    amount: float = Field(..., gt=0)
    transaction_id: str = Field(..., min_length=1)


class RefundRequest(BaseModel):
    account_id: str | None = None
    amount: float = Field(..., gt=0)
    transaction_id: str = Field(..., min_length=1)
