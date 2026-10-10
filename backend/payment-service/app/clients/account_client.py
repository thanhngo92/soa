import logging
import httpx
from app.config.env import settings
from app.utils.error_util import AppError

logger = logging.getLogger("account_client")


async def get_balance(http: httpx.AsyncClient, token: str) -> float:
    """Reads the caller's available balance from Account Service."""
    try:
        r = await http.get(
            f"{settings.ACCOUNT_SERVICE_URL}/api/accounts/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        data = r.json()
        if not data.get("success"):
            raise AppError("ACCOUNT_LOOKUP_FAILED", "Cannot read account balance", r.status_code)
        return float(data["data"]["balance"])
    except httpx.RequestError as exc:
        logger.error(f"Network error connecting to Account Service (/me): {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Account service is currently unavailable", 503)


async def deduct(http: httpx.AsyncClient, token: str, amount: float, transaction_id: str) -> dict:
    """Invokes Account Service to deduct user balance atomically."""
    try:
        r = await http.post(
            f"{settings.ACCOUNT_SERVICE_URL}/api/accounts/deduct",
            json={"amount": amount, "transaction_id": transaction_id},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Internal-Token": settings.INTERNAL_SERVICE_KEY,
            },
            timeout=10.0,
        )
        data = r.json()
        if not data.get("success"):
            err_msg = data.get("error", {}).get("message", "Deduct failed")
            raise AppError("DEDUCT_FAILED", err_msg, r.status_code)
        return data["data"]
    except httpx.RequestError as exc:
        logger.error(f"Network error connecting to Account Service (/deduct): {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Account service is currently unavailable", 503)


async def refund(http: httpx.AsyncClient, token: str, amount: float, transaction_id: str) -> bool:
    """Invokes Account Service to execute Saga compensating refund. Returns True if refunded, False otherwise."""
    try:
        r = await http.post(
            f"{settings.ACCOUNT_SERVICE_URL}/api/accounts/refund",
            json={"amount": amount, "transaction_id": transaction_id},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Internal-Token": settings.INTERNAL_SERVICE_KEY,
            },
            timeout=10.0,
        )
        data = r.json()
        if not data.get("success"):
            logger.error(f"Failed to execute Saga refund on account-service: {data.get('error')}")
            return False
        return True
    except httpx.RequestError as exc:
        logger.critical(f"Critical network failure during Saga refund on account-service: {exc}")
        return False
