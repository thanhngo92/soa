from datetime import datetime
from pymongo import ReturnDocument
from app.config.database import get_db


async def find_by_mssv(mssv: str) -> dict | None:
    return await get_db().tuitions.find_one({"student_id": mssv})


async def mark_paid(mssv: str, paid_by: str, transaction_id: str) -> dict | None:
    """Atomic UNPAID -> PAID. Returns None if already paid (Concurrency guard)."""
    return await get_db().tuitions.find_one_and_update(
        {"student_id": mssv, "status": "UNPAID"},
        {"$set": {"status": "PAID", "paid_at": datetime.utcnow(), "paid_by": paid_by, "transaction_id": transaction_id}},
        return_document=ReturnDocument.AFTER,
    )


async def revert_paid(mssv: str, transaction_id: str) -> dict | None:
    """Compensating transaction: PAID -> UNPAID (only if same transaction_id)."""
    return await get_db().tuitions.find_one_and_update(
        {"student_id": mssv, "status": "PAID", "transaction_id": transaction_id},
        {"$set": {"status": "UNPAID", "paid_at": None, "paid_by": None, "transaction_id": None}},
        return_document=ReturnDocument.AFTER,
    )
