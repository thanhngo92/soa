from datetime import datetime, timedelta
import bcrypt
import jwt

from app.config.env import settings
from app.repositories.account_repository import find_by_username, find_by_id, deduct_balance, refund_balance
from app.utils.error_util import AppError


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


async def login(username: str, password: str) -> dict:
    account = await find_by_username(username)
    if not account or not verify_password(password, account["password_hash"]):
        raise AppError("INVALID_CREDENTIALS", "Invalid username or password", 401)
    payload = {
        "sub": str(account["_id"]),
        "username": account["username"],
        "email": account["email"],
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return {"access_token": jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256"), "token_type": "bearer"}


async def get_profile(account_id: str) -> dict:
    account = await find_by_id(account_id)
    if not account:
        raise AppError("ACCOUNT_NOT_FOUND", "Account not found", 404)
    return {
        "id": str(account["_id"]),
        "username": account["username"],
        "full_name": account["full_name"],
        "email": account["email"],
        "phone": account["phone"],
        "balance": account["balance"],
    }


async def deduct(account_id: str, amount: float) -> dict:
    result = await deduct_balance(account_id, amount)
    if not result:
        raise AppError("INSUFFICIENT_BALANCE", "Insufficient balance", 400)
    return {"balance": result["balance"]}


async def refund(account_id: str, amount: float) -> dict:
    result = await refund_balance(account_id, amount)
    if not result:
        raise AppError("ACCOUNT_NOT_FOUND", "Account not found", 404)
    return {"balance": result["balance"]}
