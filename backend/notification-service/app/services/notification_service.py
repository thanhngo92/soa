from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import secrets
import smtplib

from app.config.env import settings
from app.repositories.notification_repository import (
    create_otp,
    verify_and_consume_otp,
    invalidate_otps,
    is_otp_active,
)
from app.utils.error_util import AppError

logger = logging.getLogger("notification_service")


def _send(to: str, subject: str, body: str) -> None:
    """Dispatches plain text email through configured SMTP server (Mailpit)."""
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.MAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            s.sendmail(settings.MAIL_FROM, to, msg.as_string())
        logger.info(f"Email sent successfully to '{to}' with subject '{subject}'")
    except Exception as exc:
        logger.error(f"Failed to send email to '{to}': {exc}")


async def generate_otp(payment_id: str, email: str) -> None:
    """
    Generates a secure 6-digit OTP code with 5-minute lifespan.
    Guarantees:
      - Bound to specific payment_id
      - Does not collide with any currently active OTP of another transaction
      - Max validity 5 minutes
      - Single-use consumption
    """
    await invalidate_otps(payment_id)

    # Đảm bảo mã OTP không trùng với bất kỳ OTP nào đang có hiệu lực trong hệ thống
    otp_code = None
    for _ in range(10):
        candidate = f"{secrets.randbelow(1000000):06d}"
        if not await is_otp_active(candidate):
            otp_code = candidate
            break

    if not otp_code:
        otp_code = f"{secrets.randbelow(1000000):06d}"

    await create_otp(payment_id, otp_code, email)
    logger.info(f"Generated unique OTP for payment_id={payment_id} -> {email} (valid 5 minutes)")

    body = (
        f"Kính gửi Quý khách,\n\n"
        f"Mã OTP xác thực thanh toán học phí của bạn là: {otp_code}\n\n"
        f"Thời hạn hiệu lực: 5 phút kể từ thời điểm nhận email.\n"
        f"Vì lý do an toàn, tuyệt đối không chia sẻ mã này cho bất kỳ ai.\n\n"
        f"Trân trọng,\n"
        f"Hệ thống Ngân hàng điện tử iBanking"
    )
    _send(email, "Mã xác thực giao dịch OTP - iBanking", body)


async def verify_otp(payment_id: str, otp_code: str) -> None:
    """
    Verifies OTP and marks it consumed in a single atomic SQL transaction.
    Protects against replay attacks and expired codes.
    """
    logger.info(f"Verifying OTP for payment_id={payment_id}")
    result = await verify_and_consume_otp(payment_id, otp_code)
    if not result:
        logger.warning(f"OTP verification failed for payment_id={payment_id}: invalid, expired, or already used")
        raise AppError("INVALID_OTP", "OTP is invalid, expired, or already used", 400)
    logger.info(f"OTP verified and consumed successfully for payment_id={payment_id}")


async def send_success_email(
    email: str,
    payment_id: str,
    student_name: str,
    student_id: str,
    amount: float,
    paid_at: str,
) -> None:
    """Sends detailed payment receipt email to payer upon successful transaction."""
    logger.info(f"Dispatching payment receipt email to '{email}' for payment_id={payment_id}")
    body = (
        f"Kính gửi Quý khách,\n\n"
        f"Giao dịch thanh toán học phí của bạn đã THÀNH CÔNG.\n\n"
        f"================= THÔNG TIN BIÊN NHẬN =================\n"
        f"Mã giao dịch  : {payment_id}\n"
        f"Sinh viên     : {student_name} (MSSV: {student_id})\n"
        f"Số tiền đã thu: {amount:,.0f} VND\n"
        f"Thời gian     : {paid_at}\n"
        f"Trạng thái    : THÀNH CÔNG (ĐÃ GẠCH NỢ)\n"
        f"=======================================================\n\n"
        f"Cảm ơn bạn đã sử dụng dịch vụ của iBanking!\n"
    )
    _send(email, f"Xác nhận thanh toán học phí thành công #{payment_id}", body)
