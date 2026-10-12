import aiomysql
from app.config.database import get_pool


async def create_otp(payment_id: str, otp_code: str, email: str) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO otps (payment_id, otp_code, email, expires_at, is_used) "
                "VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL 5 MINUTE), FALSE)",
                (payment_id, otp_code, email),
            )


async def verify_and_consume_otp(payment_id: str, otp_code: str) -> dict:
    """
    Xác thực và đánh dấu đã sử dụng mã OTP.
    Tuân thủ đúng quy định đề bài:
      - Tối đa 3 lần thử
      - Hạn 5 phút
      - Báo lỗi cụ thể khi quá 3 lần, hết hạn hoặc sai mã.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT id, otp_code, email, expires_at, is_used, attempts, "
                "(expires_at >= NOW()) AS is_valid_time "
                "FROM otps WHERE payment_id = %s ORDER BY id DESC LIMIT 1",
                (payment_id,),
            )
            record = await cur.fetchone()
            if not record:
                return {"status": "NOT_FOUND"}

            # Đã bị khóa do vượt quá 3 lần thử
            if record["attempts"] >= 3:
                await cur.execute("UPDATE otps SET is_used = TRUE WHERE id = %s", (record["id"],))
                return {"status": "MAX_ATTEMPTS", "attempts": record["attempts"]}

            # Đã hết hạn 5 phút
            if not record["is_valid_time"]:
                return {"status": "EXPIRED"}

            # Đã qua sử dụng
            if record["is_used"]:
                return {"status": "ALREADY_USED"}

            # Khớp mã OTP -> Xác thực thành công & Đánh dấu tiêu thụ
            if record["otp_code"] == otp_code:
                await cur.execute(
                    "UPDATE otps SET is_used = TRUE WHERE id = %s AND is_used = FALSE",
                    (record["id"],),
                )
                return {"status": "SUCCESS"}

            # Mã OTP sai -> Ghi nhận thêm 1 lần thử sai
            new_attempts = record["attempts"] + 1
            if new_attempts >= 3:
                # Đã sai đủ 3 lần -> Khóa mã OTP
                await cur.execute(
                    "UPDATE otps SET attempts = %s, is_used = TRUE WHERE id = %s",
                    (new_attempts, record["id"]),
                )
                return {"status": "MAX_ATTEMPTS", "attempts": new_attempts}
            else:
                await cur.execute(
                    "UPDATE otps SET attempts = %s WHERE id = %s",
                    (new_attempts, record["id"]),
                )
                return {
                    "status": "WRONG_CODE",
                    "attempts": new_attempts,
                    "remaining": 3 - new_attempts,
                }


async def invalidate_otps(payment_id: str) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE otps SET is_used = TRUE WHERE payment_id = %s AND is_used = FALSE",
                (payment_id,),
            )


async def is_otp_active(otp_code: str) -> bool:
    """Kiem tra ma OTP co dang co hieu luc (chua dung va chua het han) trong he thong hay khong."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id FROM otps WHERE otp_code = %s AND is_used = FALSE AND expires_at >= NOW() LIMIT 1",
                (otp_code,),
            )
            return await cur.fetchone() is not None
