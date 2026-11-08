from pydantic import BaseModel, Field


class PayTuitionRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    paid_by: str = Field(..., min_length=1)
    transaction_id: str = Field(..., min_length=1)
    semester: str | None = None
    amount: float | None = Field(default=None, gt=0)
