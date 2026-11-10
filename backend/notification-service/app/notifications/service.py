import asyncio
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import secrets
import smtplib

from app.core.config import settings
from app.notifications.repository import (
    create_otp,
    verify_and_consume_otp,
    is_otp_active,
)
from app.core.common import AppError

logger = logging.getLogger("notification_service")
_VN_TZ = timezone(timedelta(hours=7))


def _format_vn_time(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(_VN_TZ).strftime("%H:%M:%S %d/%m/%Y (GMT+7)")
    except Exception:
        return iso_str


def _send_sync(to: str, subject: str, body: str) -> None:
    msg = MIMEMultipart()
    msg["From"] = settings.MAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if settings.is_real_smtp:
        # Cấu hình có dữ liệu thật (Gmail / External SMTP) -> Gửi qua SMTP thật
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.sendmail(settings.MAIL_FROM, to, msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
                if settings.SMTP_USE_TLS:
                    s.starttls()
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.sendmail(settings.MAIL_FROM, to, msg.as_string())
        logger.info(f"Email sent via REAL SMTP ({settings.SMTP_HOST}) to '{to}' with subject '{subject}'")
    else:
        # Cấu hình là None / rỗng / mailpit -> Gửi trực tiếp qua Mailpit (No Auth, No TLS)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            s.sendmail(settings.MAIL_FROM, to, msg.as_string())
        logger.info(f"Email sent via MAILPIT ({settings.SMTP_HOST}:{settings.SMTP_PORT}) to '{to}' with subject '{subject}'")


async def _send(to: str, subject: str, body: str, raise_on_error: bool = False) -> None:
    try:
        await asyncio.to_thread(_send_sync, to, subject, body)
    except Exception as exc:
        logger.error(f"Failed to send email to '{to}': {exc}")
        if raise_on_error:
            raise AppError("MAIL_DELIVERY_ERROR", "Không thể gửi email xác thực OTP", 500)


async def generate_otp(
    payment_id: str,
    email: str,
    student_id: str | None = None,
    student_name: str | None = None,
    amount: float | None = None,
    semester: str | None = None,
) -> None:
    otp_code = None
    for _ in range(20):
        candidate = f"{secrets.randbelow(1000000):06d}"
        if not await is_otp_active(candidate):
            otp_code = candidate
            break

    if not otp_code:
        otp_code = f"{secrets.randbelow(1000000):06d}"

    await create_otp(payment_id, otp_code)
    logger.info(f"Generated OTP for payment_id={payment_id} -> {email}")

    tx_info_lines = [f"Mã giao dịch  : #{payment_id}"]
    if student_name and student_id:
        tx_info_lines.append(f"Sinh viên     : {student_name} (MSSV: {student_id})")
    elif student_id:
        tx_info_lines.append(f"Mã sinh viên  : {student_id}")
    if semester:
        tx_info_lines.append(f"Học kỳ        : {semester}")
    if amount is not None:
        tx_info_lines.append(f"Số tiền       : {amount:,.0f} VND")
    tx_info_str = "\n".join(tx_info_lines)

    body = (
        f"Kính gửi Quý khách,\n\n"
        f"Mã OTP xác thực giao dịch thanh toán học phí của bạn là: {otp_code}\n\n"
        f"--- THÔNG TIN GIAO DỊCH ---\n"
        f"{tx_info_str}\n"
        f"---------------------------\n\n"
        f"Thời hạn hiệu lực: 5 phút kể từ thời điểm nhận email (tối đa 3 lần nhập).\n"
        f"Vì lý do an toàn, tuyệt đối không chia sẻ mã này cho bất kỳ ai.\n\n"
        f"Trân trọng,\n"
        f"Hệ thống Ngân hàng điện tử iBanking"
    )
    await _send(email, f"Mã xác thực giao dịch OTP #{payment_id} - iBanking", body, raise_on_error=True)


async def verify_otp(payment_id: str, otp_code: str) -> None:
    logger.info(f"Verifying OTP for payment_id={payment_id}")
    result = await verify_and_consume_otp(payment_id, otp_code)
    status = result.get("status") if result else "NOT_FOUND"

    if status == "SUCCESS":
        logger.info(f"OTP verified for payment_id={payment_id}")
        return

    if status == "MAX_ATTEMPTS":
        logger.warning(f"OTP verification failed for payment_id={payment_id}: max attempts exceeded")
        raise AppError("OTP_MAX_ATTEMPTS_EXCEEDED", "Bạn đã nhập sai mã OTP quá 3 lần. Giao dịch đã bị khóa.", 400)

    if status == "EXPIRED":
        logger.warning(f"OTP verification failed for payment_id={payment_id}: expired")
        raise AppError("OTP_EXPIRED", "Mã OTP đã hết thời hạn hiệu lực (5 phút). Vui lòng thực hiện lại.", 400)

    if status == "ALREADY_USED":
        logger.warning(f"OTP verification failed for payment_id={payment_id}: already used")
        raise AppError("OTP_ALREADY_USED", "Mã OTP này đã được sử dụng trước đó.", 400)

    if status == "WRONG_CODE":
        remaining = result.get("remaining", 0)
        logger.warning(f"OTP verification failed for payment_id={payment_id}: wrong code (remaining={remaining})")
        raise AppError("INVALID_OTP", f"Mã OTP không chính xác. Bạn còn {remaining} lần thử.", 400)

    raise AppError("INVALID_OTP", "Mã OTP không hợp lệ hoặc không tồn tại.", 400)


async def send_success_email(
    email: str,
    payment_id: str,
    student_name: str,
    student_id: str,
    amount: float,
    paid_at: str,
    semester: str | None = None,
) -> None:
    logger.info(f"Sending payment receipt email to '{email}' for payment_id={payment_id}")
    formatted_time = _format_vn_time(paid_at)
    semester_line = f"Học kỳ        : {semester}\n" if semester else ""
    body = (
        f"Kính gửi Quý khách,\n\n"
        f"Giao dịch thanh toán học phí của bạn đã THÀNH CÔNG.\n\n"
        f"--- THÔNG TIN BIÊN NHẬN ---\n"
        f"Mã giao dịch  : #{payment_id}\n"
        f"Sinh viên     : {student_name} (MSSV: {student_id})\n"
        f"{semester_line}"
        f"Số tiền đã thu: {amount:,.0f} VND\n"
        f"Thời gian     : {formatted_time}\n"
        f"Trạng thái    : THÀNH CÔNG (ĐÃ GẠCH NỢ)\n"
        f"---------------------------\n\n"
        f"Cảm ơn bạn đã sử dụng dịch vụ của iBanking!\n"
    )
    await _send(email, f"Xác nhận thanh toán học phí thành công #{payment_id}", body, raise_on_error=False)
