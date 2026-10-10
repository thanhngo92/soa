import logging
from app.repositories.tuition_repository import find_by_mssv, mark_paid, revert_paid
from app.utils.error_util import AppError

logger = logging.getLogger("tuition_service")


async def get_tuition(mssv: str) -> dict:
    """Retrieves tuition record and payment status by student ID (MSSV)."""
    r = await find_by_mssv(mssv)
    if not r:
        logger.warning(f"Tuition query failed: Student '{mssv}' not found")
        raise AppError("STUDENT_NOT_FOUND", f"Student {mssv} not found", 404)
    return {
        "student_id":   r["student_id"],
        "student_name": r["student_name"],
        "major":        r["major"],
        "semester":     r["semester"],
        "amount":       r["amount"],
        "status":       r["status"],
    }


async def pay_tuition(mssv: str, paid_by: str, transaction_id: str, semester: str | None = None) -> dict:
    """
    Executes atomic tuition payment (status UNPAID -> PAID).
    Protected by MySQL conditional update: rowcount == 0 signals double payment attempt.
    """
    logger.info(f"Marking tuition PAID for student_id='{mssv}' semester='{semester}' by user='{paid_by}' (txn={transaction_id})")
    result = await mark_paid(mssv, paid_by, transaction_id, semester)
    if not result:
        logger.warning(f"Conflict: Tuition for student_id='{mssv}' is ALREADY PAID or was just paid concurrently")
        raise AppError("TUITION_ALREADY_PAID", "Tuition has already been paid", 409)
    logger.info(f"Tuition marked PAID successfully for student_id='{mssv}'")
    return {"student_id": mssv, "status": "PAID"}


async def revert_tuition(mssv: str, transaction_id: str | None = None, semester: str | None = None) -> dict:
    """
    Executes compensating transaction to revert tuition status back to UNPAID.
    Supports specific payment transaction_id or admin reset.
    """
    logger.info(f"Compensating transaction: Reverting tuition for student_id='{mssv}' (txn={transaction_id})")
    result = await revert_paid(mssv, transaction_id or None, semester)
    if not result:
        logger.warning(f"Revert failed for student_id='{mssv}' (mismatched transaction or already UNPAID)")
        raise AppError("REVERT_FAILED", "Revert failed: record not found or transaction mismatch", 400)
    logger.info(f"Tuition reverted to UNPAID successfully for student_id='{mssv}'")
    return {"student_id": mssv, "status": "UNPAID"}
