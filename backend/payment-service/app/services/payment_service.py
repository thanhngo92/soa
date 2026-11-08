import asyncio
import logging
from datetime import datetime, timezone
from fastapi import Request

from app.clients import account_client, notification_client, tuition_client
from app.repositories.payment_repository import (
    create_payment,
    find_by_account,
    transition_status,
    verify_otp_and_lock_processing,
)
from app.utils.error_util import AppError

logger = logging.getLogger("payment_service")


def _format_utc_iso(dt_val) -> str | None:
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            dt_val = dt_val.replace(tzinfo=timezone.utc)
        return dt_val.isoformat()
    return str(dt_val)


async def initiate(request: Request, user: dict, student_id: str) -> dict:
    http = request.app.state.http
    user_id = int(user["sub"])
    user_email = user["email"]
    cleaned_student_id = (student_id or "").strip().upper()

    tuition = await tuition_client.get_tuition(http, cleaned_student_id)
    if tuition["status"] == "PAID":
        raise AppError("TUITION_ALREADY_PAID", "Tuition has already been paid", 409)

    tuition_id = int(tuition["tuition_id"])
    amount = float(tuition["amount"])
    student_name = tuition["student_name"]

    token = request.headers.get("authorization", "").replace("Bearer ", "")
    balance = await account_client.get_balance(http, token)
    if balance < amount:
        raise AppError("INSUFFICIENT_BALANCE", "Insufficient balance", 400)

    payment_id = await create_payment({
        "account_id": user_id,
        "tuition_id": tuition_id,
        "amount": amount,
        "status": "PENDING",
    })

    try:
        await notification_client.send_otp(
            http=http,
            payment_id=payment_id,
            email=user_email,
            student_id=cleaned_student_id,
            student_name=student_name,
            amount=amount,
        )
    except Exception:
        await transition_status(payment_id, "PENDING", "FAILED", "OTP_SEND_FAILED")
        raise

    logger.info(f"Initiated payment #{payment_id} for tuition #{tuition_id} ({cleaned_student_id}, {amount:,.0f} VND)")

    return {
        "payment_id": payment_id,
        "amount": amount,
        "student_name": student_name,
    }


async def confirm(request: Request, user: dict, payment_id: str, otp_code: str) -> dict:
    http = request.app.state.http
    user_id = str(user["sub"])
    user_email = user["email"]

    lock_res = await verify_otp_and_lock_processing(
        payment_id=payment_id,
        user_id=user_id,
        otp_code=otp_code,
        verify_otp_fn=lambda pid, code: notification_client.verify_otp(http, pid, code),
    )
    lock_status = lock_res["status"]
    if lock_status == "NOT_FOUND":
        raise AppError("PAYMENT_NOT_FOUND", "Payment not found", 404)
    if lock_status == "FORBIDDEN":
        raise AppError("FORBIDDEN", "Forbidden: Not authorized for this payment", 403)
    if lock_status == "NOT_PENDING":
        raise AppError("PAYMENT_NOT_PENDING", "Payment is not in pending state", 400)
    if lock_status == "OTP_FAILED":
        raise AppError(lock_res["code"], lock_res["message"], 400)

    payment = lock_res["payment"]
    amount = float(payment["amount"])
    tuition_id = int(payment["tuition_id"])

    try:
        await account_client.deduct(http, user_id, amount, str(payment_id))
    except Exception as deduct_err:
        err_code = deduct_err.detail.get("code", "DEDUCT_FAILED") if isinstance(deduct_err, AppError) else "DEDUCT_FAILED"
        logger.warning(f"Deduct failed for payment #{payment_id} ({err_code}): {deduct_err}")
        await transition_status(payment_id, "PROCESSING", "FAILED", err_code)
        raise

    try:
        tuition_res = await tuition_client.pay(http, tuition_id=tuition_id, amount=amount)
    except Exception as exc:
        logger.error(f"Tuition pay failed for payment #{payment_id}: {exc}. Triggering refund compensation.")
        refund_ok = False
        try:
            refund_ok = await account_client.refund(http, user_id, amount, str(payment_id))
        except Exception as refund_err:
            logger.critical(f"Refund compensation failed for payment #{payment_id}: {refund_err}")

        error_code = "TUITION_MARK_FAILED" if refund_ok else "COMPENSATION_REFUND_PENDING"
        await transition_status(payment_id, "PROCESSING", "FAILED", error_code)

        if isinstance(exc, AppError) and exc.status_code == 409:
            raise AppError(
                "PAYMENT_FAILED",
                "Payment failed: tuition already paid by another transaction",
                409,
            )

        if isinstance(exc, AppError):
            msg = exc.detail.get("message", "Downstream tuition service error")
            raise AppError("PAYMENT_FAILED", f"Payment failed: {msg}", exc.status_code)
        raise AppError("PAYMENT_FAILED", f"Payment failed: {str(exc)}", 500)

    await transition_status(payment_id, "PROCESSING", "SUCCESS")
    student_id = tuition_res["student_id"]
    student_name = tuition_res["student_name"]
    semester = tuition_res.get("semester")
    paid_at = tuition_res.get("paid_at") or datetime.now(timezone.utc).isoformat()
    logger.info(f"Payment #{payment_id} completed successfully")

    await notification_client.send_success_email(http, {
        "email": user_email,
        "payment_id": str(payment_id),
        "student_name": student_name,
        "student_id": student_id,
        "amount": amount,
        "paid_at": paid_at,
    })

    return {
        "payment_id": str(payment_id),
        "status": "SUCCESS",
        "amount": amount,
        "tuition_id": tuition_id,
        "student_id": student_id,
        "student_name": student_name,
        "semester": semester,
        "paid_at": paid_at,
    }


async def history(request: Request, account_id: str) -> list:
    http = request.app.state.http
    records = await find_by_account(account_id)
    if not records:
        return []

    unique_tids = list({int(r["tuition_id"]) for r in records})
    tuition_tasks = [tuition_client.get_tuition_by_id(http, tid) for tid in unique_tids]
    tuition_results = await asyncio.gather(*tuition_tasks, return_exceptions=True)
    tuition_map = {}
    for tid, res in zip(unique_tids, tuition_results):
        if isinstance(res, dict):
            tuition_map[tid] = res

    output = []
    for r in records:
        tid = int(r["tuition_id"])
        t_info = tuition_map.get(tid, {})
        output.append({
            "payment_id": str(r["id"]),
            "tuition_id": tid,
            "student_id": t_info.get("student_id", ""),
            "student_name": t_info.get("student_name", ""),
            "semester": t_info.get("semester", ""),
            "amount": r["amount"],
            "status": r["status"],
            "created_at": _format_utc_iso(r.get("created_at")),
            "completed_at": _format_utc_iso(r.get("completed_at")),
        })
    return output
