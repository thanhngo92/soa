from bson import ObjectId
from pymongo import ReturnDocument
from app.config.database import get_db


async def find_by_username(username: str) -> dict | None:
    return await get_db().accounts.find_one({"username": username})


async def find_by_id(account_id: str) -> dict | None:
    return await get_db().accounts.find_one({"_id": ObjectId(account_id)})


async def deduct_balance(account_id: str, amount: float) -> dict | None:
    """Atomic deduction — returns updated doc only when balance >= amount."""
    return await get_db().accounts.find_one_and_update(
        {"_id": ObjectId(account_id), "balance": {"$gte": amount}},
        {"$inc": {"balance": -amount}},
        return_document=ReturnDocument.AFTER,
    )


async def refund_balance(account_id: str, amount: float) -> dict | None:
    """Compensating transaction — add amount back unconditionally."""
    return await get_db().accounts.find_one_and_update(
        {"_id": ObjectId(account_id)},
        {"$inc": {"balance": amount}},
        return_document=ReturnDocument.AFTER,
    )
