from pydantic import BaseModel


class PayTuitionRequest(BaseModel):
    student_id: str
    paid_by: str        # account_id of payer
    transaction_id: str


class RevertTuitionRequest(BaseModel):
    student_id: str
    transaction_id: str
