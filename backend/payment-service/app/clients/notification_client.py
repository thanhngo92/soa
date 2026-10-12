import logging
import httpx
from app.config.env import settings

logger = logging.getLogger("notification_client")


async def send_otp(http: httpx.AsyncClient, payment_id: str, email: str) -> None:
    """Dispatches request to generate and email OTP for a pending payment."""
    try:
        await http.post(
            f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/otp/generate",
            json={"payment_id": payment_id, "email": email},
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_KEY},
            timeout=10.0,
        )
    except Exception as exc:
        logger.error(f"Failed to request OTP from notification-service: {exc}")


async def verify_otp(http: httpx.AsyncClient, payment_id: str, otp_code: str) -> dict:
    """Dispatches request to verify and consume OTP for a payment."""
    try:
        r = await http.post(
            f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/otp/verify",
            json={"payment_id": payment_id, "otp_code": otp_code},
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_KEY},
            timeout=10.0,
        )
        data = r.json()
        if r.status_code == 200 and data.get("success"):
            return {"success": True}
        error_info = data.get("error", {})
        return {
            "success": False,
            "code": error_info.get("code", "INVALID_OTP"),
            "message": error_info.get("message", "Mã OTP không chính xác hoặc đã hết hạn"),
        }
    except Exception as exc:
        logger.error(f"Failed to verify OTP with notification-service: {exc}")
        return {"success": False, "code": "NOTIFICATION_ERROR", "message": "Không thể kết nối dịch vụ OTP"}


async def send_success_email(http: httpx.AsyncClient, payload: dict) -> None:
    """Dispatches request to send successful payment confirmation email."""
    try:
        await http.post(
            f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/email/success",
            json=payload,
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_KEY},
            timeout=10.0,
        )
    except Exception as exc:
        logger.error(f"Failed to send success email via notification-service: {exc}")
