import logging
from datetime import datetime, timezone
from fastapi import Request

from app.clients import account_client, notification_client, tuition_client
from app.repositories.payment_repository import (
    create_payment,
    find_by_account,
    find_by_id,
    transition_status,
)
from app.utils.error_util import AppError

logger = logging.getLogger("payment_service")


async def initiate(request: Request, user: dict, student_id: str) -> dict:
    """Khoi tao giao dich thanh toan hoc phi va gui OTP xac thuc."""
    http = request.app.state.http
    user_id = user["sub"]
    user_email = user["email"]

    tuition = await tuition_client.get_tuition(http, student_id)
    if tuition["status"] == "PAID":
        raise AppError("TUITION_ALREADY_PAID", "Tuition has already been paid", 409)

    amount = float(tuition["amount"])
    student_name = tuition["student_name"]
    semester = tuition.get("semester")

    token = request.headers.get("authorization", "").replace("Bearer ", "")
    balance = await account_client.get_balance(http, token)
    if balance < amount:
        raise AppError("INSUFFICIENT_BALANCE", "Insufficient balance", 400)

    payment_id = await create_payment({
        "account_id": user_id,
        "email": user_email,
        "student_id": student_id,
        "student_name": student_name,
        "amount": amount,
        "status": "PENDING",
        "semester": semester,
    })

    # Gui OTP qua email nguoi dung
    await notification_client.send_otp(http, payment_id, user_email)
    logger.info(f"Initiated payment #{payment_id} for student {student_id} ({amount:,.0f} VND)")

    return {
        "payment_id": payment_id,
        "amount": amount,
        "student_name": student_name,
    }


async def confirm(request: Request, user: dict, payment_id: str, otp_code: str) -> dict:
    """Xac nhan OTP va dieu phoi quy trinh thanh toan Saga."""
    http = request.app.state.http
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    user_id = user["sub"]
    user_email = user["email"]

    payment = await find_by_id(payment_id)
    if not payment:
        raise AppError("PAYMENT_NOT_FOUND", "Payment not found", 404)
    if payment["status"] != "PENDING":
        raise AppError("PAYMENT_NOT_PENDING", "Payment is not in pending state", 400)
    if payment["account_id"] != user_id:
        raise AppError("FORBIDDEN", "Forbidden: Not authorized for this payment", 403)

    amount = payment["amount"]
    student_id = payment["student_id"]
    student_name = payment["student_name"]
    semester = payment.get("semester")

    # 1. Xac thuc ma OTP
    otp_valid = await notification_client.verify_otp(http, payment_id, otp_code)
    if not otp_valid:
        raise AppError("INVALID_OTP", "OTP is invalid, expired, or already used", 400)

    # 2. Khoa trang thai FSM: PENDING -> PROCESSING
    transitioned = await transition_status(payment_id, "PENDING", "PROCESSING")
    if not transitioned:
        raise AppError("PAYMENT_NOT_PENDING", "Payment transaction is already being processed", 400)

    # 3. Kiem tra lai tinh hop le cua giao dich va so du kha dung truoc khi trích nợ
    balance = await account_client.get_balance(http, token)
    if balance < amount:
        logger.warning(f"Re-check balance failed for payment #{payment_id}: balance={balance:,.0f} < amount={amount:,.0f}")
        await transition_status(payment_id, "PROCESSING", "FAILED", "INSUFFICIENT_BALANCE")
        raise AppError("INSUFFICIENT_BALANCE", "Insufficient balance", 400)

    # 4. Buoc 1 Saga: Tru tien tai khoan (Atomic Row-Locking)
    try:
        await account_client.deduct(http, token, amount, payment_id)
    except Exception as deduct_err:
        logger.warning(f"Deduct failed for payment #{payment_id}: {deduct_err}")
        await transition_status(payment_id, "PROCESSING", "FAILED", "DEDUCT_FAILED")
        raise

    # 4. Buoc 2 Saga: Gach no hoc phi sinh vien
    try:
        await tuition_client.pay(http, student_id, user_id, payment_id, semester)
    except Exception as exc:
        # Gach no loi: kich hoat giao dich bu tru hoan lai tien cho nguoi dung
        logger.error(f"Tuition pay failed for payment #{payment_id}: {exc}. Triggering refund compensation.")
        refund_ok = False
        try:
            refund_ok = await account_client.refund(http, token, amount, payment_id)
        except Exception as refund_err:
            logger.critical(f"Critical: refund compensation failed for payment #{payment_id}: {refund_err}")

        error_code = "TUITION_MARK_FAILED" if refund_ok else "COMPENSATION_REFUND_PENDING"
        await transition_status(payment_id, "PROCESSING", "FAILED", error_code)

        if isinstance(exc, AppError):
            raise AppError("PAYMENT_FAILED", "Payment failed: tuition already paid by another transaction", 409)
        raise AppError("PAYMENT_FAILED", f"Payment failed: {str(exc)}", 500)

    # 5. Hoan tat giao dich thanh cong
    await transition_status(payment_id, "PROCESSING", "SUCCESS")
    paid_at = datetime.now(timezone.utc).isoformat()
    logger.info(f"Payment #{payment_id} completed successfully")

    # Gui email bien nhan
    await notification_client.send_success_email(http, {
        "email": user_email,
        "payment_id": payment_id,
        "student_name": student_name,
        "student_id": student_id,
        "amount": amount,
        "paid_at": paid_at,
    })

    return {
        "payment_id": payment_id,
        "status": "SUCCESS",
        "amount": amount,
        "student_id": student_id,
        "student_name": student_name,
        "paid_at": paid_at,
    }


async def history(account_id: str) -> list:
    """Lay danh sach lich su giao dich thanh toan cua tai khoan."""
    records = await find_by_account(account_id)
    return [{
        "payment_id": str(r["id"]),
        "student_id": r["student_id"],
        "student_name": r["student_name"],
        "amount": r["amount"],
        "status": r["status"],
        "created_at": r["created_at"].isoformat(),
        "completed_at": r["completed_at"].isoformat() if r.get("completed_at") else None,
    } for r in records]
