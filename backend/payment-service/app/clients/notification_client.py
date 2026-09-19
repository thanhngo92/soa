import httpx
from app.config.env import settings


async def send_otp(http: httpx.AsyncClient, payment_id: str, email: str) -> None:
    await http.post(
        f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/otp/generate",
        json={"payment_id": payment_id, "email": email},
    )


async def verify_otp(http: httpx.AsyncClient, payment_id: str, otp_code: str) -> bool:
    r = await http.post(
        f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/otp/verify",
        json={"payment_id": payment_id, "otp_code": otp_code},
    )
    return r.json().get("success", False)


async def send_success_email(http: httpx.AsyncClient, payload: dict) -> None:
    await http.post(
        f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/email/success",
        json=payload,
    )
