import httpx
from app.config.env import settings
from app.utils.error_util import AppError


async def deduct(http: httpx.AsyncClient, token: str, amount: float, transaction_id: str) -> dict:
    r = await http.post(
        f"{settings.ACCOUNT_SERVICE_URL}/api/accounts/deduct",
        json={"amount": amount, "transaction_id": transaction_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = r.json()
    if not data.get("success"):
        raise AppError("DEDUCT_FAILED", data.get("error", {}).get("message", "Deduct failed"), 400)
    return data["data"]


async def refund(http: httpx.AsyncClient, token: str, amount: float, transaction_id: str) -> None:
    await http.post(
        f"{settings.ACCOUNT_SERVICE_URL}/api/accounts/refund",
        json={"amount": amount, "transaction_id": transaction_id},
        headers={"Authorization": f"Bearer {token}"},
    )
