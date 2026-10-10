from pydantic import BaseModel


class PayTuitionRequest(BaseModel):
    student_id: str
    paid_by: str        # account_id of payer
    transaction_id: str
    semester: str | None = None


class RevertTuitionRequest(BaseModel):
    student_id: str
    transaction_id: str | None = None
    semester: str | None = None
