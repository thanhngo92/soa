from datetime import datetime
from pymongo import ReturnDocument
from app.config.database import get_db


async def create_otp(payment_id: str, otp_code: str, email: str, expires_at: datetime) -> None:
    await get_db().otps.insert_one({
        "payment_id": payment_id, "otp_code": otp_code, "email": email,
        "expires_at": expires_at, "is_used": False, "created_at": datetime.utcnow(),
    })


async def verify_and_consume_otp(payment_id: str, otp_code: str) -> dict | None:
    """Atomic: find valid OTP and mark used in one operation (Concurrency guard)."""
    return await get_db().otps.find_one_and_update(
        {"payment_id": payment_id, "otp_code": otp_code, "is_used": False, "expires_at": {"$gte": datetime.utcnow()}},
        {"$set": {"is_used": True}},
        return_document=ReturnDocument.AFTER,
    )


async def invalidate_otps(payment_id: str) -> None:
    await get_db().otps.update_many({"payment_id": payment_id, "is_used": False}, {"$set": {"is_used": True}})
