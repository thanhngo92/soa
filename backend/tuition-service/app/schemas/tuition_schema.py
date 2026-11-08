from pydantic import BaseModel, Field


class PayTuitionRequest(BaseModel):
    tuition_id: int | None = None
    student_id: str | None = None
    semester: str | None = None
    amount: float | None = Field(default=None, gt=0)
