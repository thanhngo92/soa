import httpx
from app.config.env import settings
from app.utils.error_util import AppError


async def get_tuition(http: httpx.AsyncClient, mssv: str) -> dict:
    r = await http.get(f"{settings.TUITION_SERVICE_URL}/api/tuitions/students/{mssv}")
    data = r.json()
    if not data.get("success"):
        raise AppError("TUITION_NOT_FOUND", data.get("error", {}).get("message", "Not found"), 404)
    return data["data"]


async def pay(http: httpx.AsyncClient, student_id: str, paid_by: str, transaction_id: str) -> dict:
    r = await http.post(
        f"{settings.TUITION_SERVICE_URL}/api/tuitions/pay",
        json={"student_id": student_id, "paid_by": paid_by, "transaction_id": transaction_id},
    )
    data = r.json()
    if not data.get("success"):
        raise AppError("PAY_TUITION_FAILED", data.get("error", {}).get("message", "Pay failed"), r.status_code)
    return data["data"]


async def revert(http: httpx.AsyncClient, student_id: str, transaction_id: str) -> None:
    await http.post(
        f"{settings.TUITION_SERVICE_URL}/api/tuitions/revert",
        json={"student_id": student_id, "transaction_id": transaction_id},
    )
