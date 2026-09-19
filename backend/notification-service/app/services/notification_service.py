import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config.env import settings
from app.repositories.notification_repository import create_otp, verify_and_consume_otp, invalidate_otps
from app.utils.error_util import AppError


def _send(to: str, subject: str, body: str) -> None:
    msg = MIMEMultipart()
    msg["From"], msg["To"], msg["Subject"] = settings.MAIL_FROM, to, subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        s.sendmail(settings.MAIL_FROM, to, msg.as_string())


async def generate_otp(payment_id: str, email: str) -> None:
    await invalidate_otps(payment_id)
    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    await create_otp(payment_id, otp_code, email, expires_at)
    _send(email, "Ma xac thuc OTP", f"Ma OTP: {otp_code}\nHieu luc 5 phut. Khong chia se ma nay.")


async def verify_otp(payment_id: str, otp_code: str) -> None:
    result = await verify_and_consume_otp(payment_id, otp_code)
    if not result:
        raise AppError("INVALID_OTP", "OTP is invalid, expired, or already used", 400)


async def send_success_email(email: str, payment_id: str, student_name: str, student_id: str, amount: float, paid_at: str) -> None:
    body = (
        f"Thanh toan hoc phi thanh cong!\n\n"
        f"Ma giao dich: {payment_id}\n"
        f"Sinh vien: {student_name} ({student_id})\n"
        f"So tien: {amount:,.0f} VND\n"
        f"Thoi gian: {paid_at}"
    )
    _send(email, "Xac nhan thanh toan hoc phi", body)
