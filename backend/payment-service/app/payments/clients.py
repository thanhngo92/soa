import logging
import httpx
from app.core.config import settings
from app.core.common import AppError

logger = logging.getLogger("clients")


# --- Account Client ---

async def get_account_balance(http: httpx.AsyncClient, token: str) -> float:
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


async def deduct_account(
    http: httpx.AsyncClient,
    account_id: str,
    amount: float,
    transaction_id: str,
) -> dict:
    payload = {"account_id": str(account_id), "amount": amount, "transaction_id": transaction_id}
    headers = {"X-Internal-Token": settings.INTERNAL_SERVICE_KEY}
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


async def refund_account(
    http: httpx.AsyncClient,
    account_id: str,
    amount: float,
    transaction_id: str,
) -> bool:
    payload = {"account_id": str(account_id), "amount": amount, "transaction_id": transaction_id}
    headers = {"X-Internal-Token": settings.INTERNAL_SERVICE_KEY}
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


# --- Tuition Client ---

async def get_tuition(http: httpx.AsyncClient, mssv: str) -> dict:
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


async def pay_tuition(
    http: httpx.AsyncClient,
    tuition_id: int,
    amount: float | None = None,
) -> dict:
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


# --- Notification Client ---

async def send_otp(
    http: httpx.AsyncClient,
    payment_id: str,
    email: str,
    student_id: str | None = None,
    student_name: str | None = None,
    amount: float | None = None,
    semester: str | None = None,
) -> None:
    payload: dict = {"payment_id": payment_id, "email": email}
    if student_id:
        payload["student_id"] = student_id
    if student_name:
        payload["student_name"] = student_name
    if amount is not None:
        payload["amount"] = amount
    if semester:
        payload["semester"] = semester

    try:
        r = await http.post(
            f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/otp/generate",
            json=payload,
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_KEY},
            timeout=10.0,
        )
        data = r.json()
        if r.status_code != 200 or not data.get("success"):
            err_msg = data.get("error", {}).get("message", "Failed to generate and send OTP")
            raise AppError("OTP_SEND_FAILED", err_msg, r.status_code if r.status_code >= 400 else 500)
    except AppError:
        raise
    except Exception as exc:
        logger.error(f"Failed to request OTP from notification-service: {exc}")
        raise AppError("SERVICE_UNAVAILABLE", "Notification service is currently unavailable", 503)


async def verify_otp(http: httpx.AsyncClient, payment_id: str, otp_code: str) -> dict:
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
    try:
        await http.post(
            f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/email/success",
            json=payload,
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_KEY},
            timeout=10.0,
        )
    except Exception as exc:
        logger.error(f"Failed to send success email via notification-service: {exc}")
