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
            err_code = data.get("error", {}).get("code", "ACCOUNT_LOOKUP_FAILED")
            err_msg = data.get("error", {}).get("message", "Cannot read account balance")
            raise AppError(err_code, err_msg, r.status_code)
        return float(data["data"]["balance"])
    except httpx.RequestError as exc:
        logger.error(f"Network error connecting to Account Service (/me): {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Account service is currently unavailable", 503)


async def deduct(
    http: httpx.AsyncClient,
    token: str,
    amount: float,
    transaction_id: str,
    account_id: str | None = None,
) -> dict:
    """Invokes Account Service to deduct user balance atomically."""
    payload: dict = {"amount": amount, "transaction_id": transaction_id}
    if account_id:
        payload["account_id"] = str(account_id)
    headers = {"X-Internal-Token": settings.INTERNAL_SERVICE_KEY}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = await http.post(
            f"{settings.ACCOUNT_SERVICE_URL}/api/accounts/deduct",
            json=payload,
            headers=headers,
            timeout=10.0,
        )
        data = r.json()
        if not data.get("success"):
            err_code = data.get("error", {}).get("code", "DEDUCT_FAILED")
            err_msg = data.get("error", {}).get("message", "Deduct failed")
            raise AppError(err_code, err_msg, r.status_code)
        return data["data"]
    except httpx.RequestError as exc:
        logger.error(f"Network error connecting to Account Service (/deduct): {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Account service is currently unavailable", 503)


async def refund(
    http: httpx.AsyncClient,
    token: str,
    amount: float,
    transaction_id: str,
    account_id: str | None = None,
) -> bool:
    """
    Invokes Account Service to execute Saga compensating refund.
    Passes account_id directly with X-Internal-Token so Saga rollback succeeds even if user JWT expired.
    """
    payload: dict = {"amount": amount, "transaction_id": transaction_id}
    if account_id:
        payload["account_id"] = str(account_id)
    headers = {"X-Internal-Token": settings.INTERNAL_SERVICE_KEY}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = await http.post(
            f"{settings.ACCOUNT_SERVICE_URL}/api/accounts/refund",
            json=payload,
            headers=headers,
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
