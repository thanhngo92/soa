from app.repositories.tuition_repository import find_by_mssv, mark_paid, revert_paid
from app.utils.error_util import AppError


async def get_tuition(mssv: str) -> dict:
    r = await find_by_mssv(mssv)
    if not r:
        raise AppError("STUDENT_NOT_FOUND", f"Student {mssv} not found", 404)
    return {"student_id": r["student_id"], "student_name": r["student_name"],
            "major": r["major"], "semester": r["semester"], "amount": r["amount"], "status": r["status"]}


async def pay_tuition(mssv: str, paid_by: str, transaction_id: str) -> dict:
    result = await mark_paid(mssv, paid_by, transaction_id)
    if not result:
        raise AppError("TUITION_ALREADY_PAID", "Tuition has already been paid", 409)
    return {"student_id": mssv, "status": "PAID"}


async def revert_tuition(mssv: str, transaction_id: str) -> dict:
    result = await revert_paid(mssv, transaction_id)
    if not result:
        raise AppError("REVERT_FAILED", "Revert failed: record not found or transaction mismatch", 400)
    return {"student_id": mssv, "status": "UNPAID"}
