from datetime import datetime, timezone
from fastapi import Request

from app.repositories.payment_repository import create_payment, find_by_id, update_status, find_by_account
from app.clients import account_client, tuition_client, notification_client
from app.utils.error_util import AppError


async def initiate(request: Request, user: dict, student_id: str) -> dict:
    http = request.app.state.http
    token = request.headers.get("authorization", "").replace("Bearer ", "")

    tuition = await tuition_client.get_tuition(http, student_id)
    if tuition["status"] == "PAID":
        raise AppError("TUITION_ALREADY_PAID", "Tuition has already been paid", 409)

    payment_id = await create_payment({
        "account_id": user["sub"],
        "email": user["email"],
        "student_id": student_id,
        "student_name": tuition["student_name"],
        "amount": tuition["amount"],
        "status": "PENDING",
    })

    await notification_client.send_otp(http, payment_id, user["email"])

    return {"payment_id": payment_id, "amount": tuition["amount"], "student_name": tuition["student_name"]}


async def confirm(request: Request, user: dict, payment_id: str, otp_code: str) -> dict:
    http = request.app.state.http
    token = request.headers.get("authorization", "").replace("Bearer ", "")

    payment = await find_by_id(payment_id)
    if not payment:
        raise AppError("PAYMENT_NOT_FOUND", "Payment not found", 404)
    if payment["status"] != "PENDING":
        raise AppError("PAYMENT_NOT_PENDING", "Payment is not in pending state", 400)
    if payment["account_id"] != user["sub"]:
        raise AppError("FORBIDDEN", "Forbidden", 403)

    otp_valid = await notification_client.verify_otp(http, payment_id, otp_code)
    if not otp_valid:
        raise AppError("INVALID_OTP", "OTP is invalid, expired, or already used", 400)

    amount = payment["amount"]
    student_id = payment["student_id"]

    # Step 1: Deduct balance (atomic in account-service)
    await account_client.deduct(http, token, amount, payment_id)

    # Step 2: Mark tuition paid (atomic in tuition-service)
    try:
        await tuition_client.pay(http, student_id, user["sub"], payment_id)
    except AppError:
        # Compensating transaction
        await account_client.refund(http, token, amount, payment_id)
        await update_status(payment_id, "FAILED", "TUITION_MARK_FAILED")
        raise AppError("PAYMENT_FAILED", "Payment failed: tuition already paid by another transaction", 409)

    await update_status(payment_id, "SUCCESS")
    paid_at = datetime.now(timezone.utc).isoformat()

    await notification_client.send_success_email(http, {
        "email": user["email"], "payment_id": payment_id,
        "student_name": payment["student_name"], "student_id": student_id,
        "amount": amount, "paid_at": paid_at,
    })

    return {"payment_id": payment_id, "status": "SUCCESS", "amount": amount, "student_id": student_id, "paid_at": paid_at}


async def history(account_id: str) -> list:
    records = await find_by_account(account_id)
    return [{
        "payment_id": str(r["_id"]),
        "student_id": r["student_id"],
        "student_name": r["student_name"],
        "amount": r["amount"],
        "status": r["status"],
        "created_at": r["created_at"].isoformat(),
        "completed_at": r["completed_at"].isoformat() if r.get("completed_at") else None,
    } for r in records]
