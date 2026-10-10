import logging
import httpx
from app.config.env import settings
from app.utils.error_util import AppError

logger = logging.getLogger("tuition_client")


async def get_tuition(http: httpx.AsyncClient, mssv: str) -> dict:
    """Queries Tuition Service for student tuition status and amount."""
    try:
        r = await http.get(f"{settings.TUITION_SERVICE_URL}/api/tuitions/students/{mssv}", timeout=10.0)
        data = r.json()
        if not data.get("success"):
            err_msg = data.get("error", {}).get("message", "Not found")
            raise AppError("TUITION_NOT_FOUND", err_msg, r.status_code)
        return data["data"]
    except httpx.RequestError as exc:
        logger.error(f"Network error connecting to Tuition Service (/students): {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Tuition service is currently unavailable", 503)


async def pay(http: httpx.AsyncClient, student_id: str, paid_by: str, transaction_id: str, semester: str | None = None) -> dict:
    """Invokes Tuition Service to mark tuition as PAID atomically for targeted semester."""
    payload = {"student_id": student_id, "paid_by": paid_by, "transaction_id": transaction_id}
    if semester:
        payload["semester"] = semester
    try:
        r = await http.post(
            f"{settings.TUITION_SERVICE_URL}/api/tuitions/pay",
            json=payload,
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_KEY},
            timeout=10.0,
        )
        data = r.json()
        if not data.get("success"):
            err_msg = data.get("error", {}).get("message", "Pay failed")
            raise AppError("PAY_TUITION_FAILED", err_msg, r.status_code)
        return data["data"]
    except httpx.RequestError as exc:
        logger.error(f"Network error connecting to Tuition Service (/pay): {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Tuition service is currently unavailable", 503)
