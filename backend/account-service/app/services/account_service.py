from datetime import datetime, timedelta, timezone
import logging
import bcrypt
import jwt

from app.config.env import settings
from app.repositories.account_repository import (
    find_by_username,
    find_by_id,
    deduct_balance,
    refund_balance,
    get_account_transactions,
)
from app.utils.error_util import AppError

logger = logging.getLogger("account_service")


def _verify_password(plain: str, hashed: str) -> bool:
    """Verifies plain text password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


async def login(username: str, password: str) -> dict:
    """Authenticates user credentials and returns JWT bearer token."""
    account = await find_by_username(username)
    if not account or not _verify_password(password, account["password_hash"]):
        logger.warning(f"Login failed: Invalid credentials for username '{username}'")
        raise AppError("INVALID_CREDENTIALS", "Invalid username or password", 401)

    payload = {
        "sub":      str(account["id"]),
        "username": account["username"],
        "email":    account["email"],
        "exp":      datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    logger.info(f"User '{username}' (id={account['id']}) logged in successfully")
    return {"access_token": token, "token_type": "bearer"}


async def get_profile(account_id: str) -> dict:
    """Fetches user profile and current available balance."""
    account = await find_by_id(account_id)
    if not account:
        raise AppError("ACCOUNT_NOT_FOUND", "Account not found", 404)
    return {
        "id":        str(account["id"]),
        "username":  account["username"],
        "full_name": account["full_name"],
        "email":     account["email"],
        "phone":     account["phone"],
        "balance":   account["balance"],
    }


async def deduct(account_id: str, amount: float, transaction_id: str = "") -> dict:
    """
    Executes atomic balance deduction protected by InnoDB row-level lock and audit ledger.
    Guarantees balance will never become negative and deduplication via Idempotency key.
    """
    logger.info(f"Deducting {amount:,.0f} VND from account_id={account_id} (txn={transaction_id})")
    result = await deduct_balance(account_id, amount, transaction_id)
    if not result:
        logger.warning(f"Deduction rejected: Insufficient balance for account_id={account_id} (amount={amount:,.0f} VND)")
        raise AppError("INSUFFICIENT_BALANCE", "Insufficient balance", 400)
    logger.info(f"Deducted {amount:,.0f} VND successfully. New balance: {result['balance']:,.0f} VND")
    return {"balance": result["balance"]}


async def refund(account_id: str, amount: float, transaction_id: str = "") -> dict:
    """
    Executes compensating transaction (Saga Rollback) with idempotency & audit ledger.
    Restores deducted amount if subsequent payment steps fail.
    """
    logger.info(f"Refunding {amount:,.0f} VND to account_id={account_id} (Saga compensation, txn={transaction_id})")
    result = await refund_balance(account_id, amount, transaction_id)
    if not result:
        logger.error(f"Refund failed: Account not found for account_id={account_id}")
        raise AppError("ACCOUNT_NOT_FOUND", "Account not found", 404)
    logger.info(f"Refund completed successfully. Restored balance: {result['balance']:,.0f} VND")
    return {"balance": result["balance"]}


async def get_statement(account_id: str, limit: int = 100) -> list[dict]:
    """Retrieves account statement (balance history ledger) for authenticated user."""
    return await get_account_transactions(account_id, limit)

