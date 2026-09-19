from bson import ObjectId
from datetime import datetime
from app.config.database import get_db


async def create_payment(data: dict) -> str:
    data["created_at"] = datetime.utcnow()
    data["completed_at"] = None
    result = await get_db().payments.insert_one(data)
    return str(result.inserted_id)


async def find_by_id(payment_id: str) -> dict | None:
    return await get_db().payments.find_one({"_id": ObjectId(payment_id)})


async def update_status(payment_id: str, status: str, error_code: str | None = None) -> None:
    patch = {"status": status, "completed_at": datetime.utcnow()}
    if error_code:
        patch["error_code"] = error_code
    await get_db().payments.update_one({"_id": ObjectId(payment_id)}, {"$set": patch})


async def find_by_account(account_id: str) -> list[dict]:
    cursor = get_db().payments.find({"account_id": account_id}).sort("created_at", -1)
    return await cursor.to_list(length=100)
