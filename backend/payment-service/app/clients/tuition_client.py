import logging
import httpx
from app.config.env import settings
from app.utils.error_util import AppError

logger = logging.getLogger("tuition_client")


async def get_tuition(http: httpx.AsyncClient, mssv: str) -> dict:
    """Queries Tuition Service for student tuition status and amount by MSSV."""
    try:
        r = await http.get(
            f"{settings.TUITION_SERVICE_URL}/api/tuitions/students/{mssv}",
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_KEY},
            timeout=10.0,
        )
        data = r.json()
        if not data.get("success"):
            err_code = data.get("error", {}).get("code", "TUITION_NOT_FOUND")
            err_msg = data.get("error", {}).get("message", "Not found")
            raise AppError(err_code, err_msg, r.status_code)
        return data["data"]
    except httpx.RequestError as exc:
        logger.error(f"Network error connecting to Tuition Service (/students): {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Tuition service is currently unavailable", 503)


async def get_tuition_by_id(http: httpx.AsyncClient, tuition_id: int) -> dict:
    """Queries Tuition Service for tuition and student details by tuition primary key ID."""
    try:
        r = await http.get(
            f"{settings.TUITION_SERVICE_URL}/api/tuitions/records/{tuition_id}",
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_KEY},
            timeout=10.0,
        )
        data = r.json()
        if not data.get("success"):
            err_code = data.get("error", {}).get("code", "TUITION_NOT_FOUND")
            err_msg = data.get("error", {}).get("message", "Not found")
            raise AppError(err_code, err_msg, r.status_code)
        return data["data"]
    except httpx.RequestError as exc:
        logger.error(f"Network error connecting to Tuition Service (/records/{tuition_id}): {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Tuition service is currently unavailable", 503)


async def pay(
    http: httpx.AsyncClient,
    tuition_id: int,
    amount: float | None = None,
) -> dict:
    """Invokes Tuition Service to mark tuition as PAID atomically by tuition_id and amount."""
    payload: dict = {"tuition_id": int(tuition_id)}
    if amount is not None:
        payload["amount"] = amount
    try:
        r = await http.post(
            f"{settings.TUITION_SERVICE_URL}/api/tuitions/pay",
            json=payload,
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_KEY},
            timeout=10.0,
        )
        data = r.json()
        if not data.get("success"):
            err_code = data.get("error", {}).get("code", "PAY_TUITION_FAILED")
            err_msg = data.get("error", {}).get("message", "Pay failed")
            raise AppError(err_code, err_msg, r.status_code)
        return data["data"]
    except httpx.RequestError as exc:
        logger.error(f"Network error connecting to Tuition Service (/pay): {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Tuition service is currently unavailable", 503)
