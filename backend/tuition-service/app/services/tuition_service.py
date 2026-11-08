from datetime import datetime, timezone
import logging
import re
from app.repositories.tuition_repository import find_by_id, find_by_mssv, mark_paid
from app.utils.error_util import AppError

logger = logging.getLogger("tuition_service")
_MSSV_PATTERN = re.compile(r"^[0-9A-Za-z]{6,10}$")


def _format_dt(dt_val) -> str | None:
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            dt_val = dt_val.replace(tzinfo=timezone.utc)
        return dt_val.isoformat()
    return str(dt_val)


def _serialize_tuition(r: dict) -> dict:
    return {
        "tuition_id":   int(r["id"]),
        "student_id":   r["student_id"],
        "student_name": r["student_name"],
        "major":        r["major"],
        "semester":     r["semester"],
        "amount":       r["amount"],
        "status":       r["status"],
        "paid_at":      _format_dt(r.get("paid_at")),
    }


async def get_tuition(mssv: str) -> dict:
    """Retrieves tuition record and payment status by student ID (MSSV)."""
    cleaned_mssv = (mssv or "").strip().upper()
    if not _MSSV_PATTERN.match(cleaned_mssv):
        raise AppError("INVALID_MSSV_FORMAT", "Mã số sinh viên không hợp lệ (cần từ 6 đến 10 ký tự chữ và số)", 400)

    r = await find_by_mssv(cleaned_mssv)
    if not r:
        logger.warning(f"Tuition query failed: Student '{cleaned_mssv}' not found")
        raise AppError("STUDENT_NOT_FOUND", f"Student {cleaned_mssv} not found", 404)
    return _serialize_tuition(r)


async def get_tuition_by_id(tuition_id: int) -> dict:
    """Retrieves tuition and student info by tuition primary key ID."""
    r = await find_by_id(tuition_id)
    if not r:
        raise AppError("TUITION_NOT_FOUND", f"Tuition #{tuition_id} not found", 404)
    return _serialize_tuition(r)


async def pay_tuition(
    tuition_id: int | None = None,
    mssv: str | None = None,
    semester: str | None = None,
    amount: float | None = None,
) -> dict:
    """Executes atomic tuition payment (status UNPAID -> PAID) with row-level lock and amount verification."""
    logger.info(
        f"Marking tuition PAID for tuition_id={tuition_id} student_id='{mssv}' semester='{semester}' amount={amount}"
    )
    result = await mark_paid(tuition_id=tuition_id, mssv=mssv, semester=semester, expected_amount=amount)
    if not result:
        logger.warning(f"Conflict: Tuition (id={tuition_id}, student_id='{mssv}') is ALREADY PAID or amount mismatched")
        raise AppError("TUITION_ALREADY_PAID", "Tuition has already been paid", 409)
    logger.info(f"Tuition #{result['id']} marked PAID successfully for student_id='{result['student_id']}'")
    return {
        "tuition_id":   int(result["id"]),
        "student_id":   result["student_id"],
        "student_name": result["student_name"],
        "semester":     result["semester"],
        "status":       "PAID",
        "paid_at":      _format_dt(result.get("paid_at")),
    }
