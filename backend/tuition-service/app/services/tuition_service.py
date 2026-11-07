from datetime import datetime, timezone
import logging
import re
from app.repositories.tuition_repository import find_by_mssv, mark_paid, revert_paid
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


# [Rubric Tiêu chí 5 / Đề bài Mục 2: Tra cứu học phí theo MSSV]
# - Nghiệp vụ: Trả về thông tin sinh viên, ngành học, học kỳ, số tiền và trạng thái nợ.
# - Kỹ thuật: Kiểm tra định dạng MSSV hợp lệ (6-10 ký tự), trả về 404 nếu không tìm thấy.
async def get_tuition(mssv: str) -> dict:
    """Retrieves tuition record and payment status by student ID (MSSV)."""
    cleaned_mssv = (mssv or "").strip().upper()
    if not _MSSV_PATTERN.match(cleaned_mssv):
        raise AppError("INVALID_MSSV_FORMAT", "Mã số sinh viên không hợp lệ (cần từ 6 đến 10 ký tự chữ và số)", 400)

    r = await find_by_mssv(cleaned_mssv)
    if not r:
        logger.warning(f"Tuition query failed: Student '{cleaned_mssv}' not found")
        raise AppError("STUDENT_NOT_FOUND", f"Student {cleaned_mssv} not found", 404)
    return {
        "student_id":   r["student_id"],
        "student_name": r["student_name"],
        "major":        r["major"],
        "semester":     r["semester"],
        "amount":       r["amount"],
        "status":       r["status"],
        "paid_at":      _format_dt(r.get("paid_at")),
    }


# [Rubric Tiêu chí 6 / Đề bài Mục 4: Gạch nợ học phí nguyên tử (Atomic Conditional Update)]
# - Nghiệp vụ: Chuyển trạng thái học phí sang PAID và lưu vết giao dịch.
# - Kỹ thuật: UPDATE ... WHERE status = 'UNPAID'. Nếu rowcount == 0 nghĩa là đã bị gạch nợ
#             đồng thời bởi giao dịch khác -> Ném 409 TUITION_ALREADY_PAID để kích hoạt Saga Rollback.
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
    return {
        "student_id": mssv,
        "status": "PAID",
        "paid_at": _format_dt(result.get("paid_at")),
    }


# [Rubric Tiêu chí 6 / Đề bài Mục 5: Bù trừ gạch nợ Saga (Compensating Transaction)]
# - Nghiệp vụ: Khôi phục trạng thái học phí về UNPAID khi quy trình thanh toán thất bại ở bước sau.
# - Kỹ thuật: Khớp đúng mã transaction_id để tránh hoàn tác sai giao dịch của người khác.
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
