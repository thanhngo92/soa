from datetime import datetime
import aiomysql
from app.config.database import get_pool


async def create_otp(payment_id: str, otp_code: str, email: str, expires_at: datetime) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO otps (payment_id, otp_code, email, expires_at, is_used) "
                "VALUES (%s, %s, %s, %s, FALSE)",
                (payment_id, otp_code, email, expires_at),
            )


async def verify_and_consume_otp(payment_id: str, otp_code: str) -> dict | None:
    """Atomic: find valid OTP and mark used in one operation (Concurrency guard via MySQL row lock)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "UPDATE otps SET is_used = TRUE "
                "WHERE payment_id = %s AND otp_code = %s AND is_used = FALSE AND expires_at >= NOW()",
                (payment_id, otp_code),
            )
            if cur.rowcount == 0:
                return None
            await cur.execute(
                "SELECT * FROM otps WHERE payment_id = %s AND otp_code = %s ORDER BY id DESC LIMIT 1",
                (payment_id, otp_code),
            )
            return await cur.fetchone()


async def invalidate_otps(payment_id: str) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE otps SET is_used = TRUE WHERE payment_id = %s AND is_used = FALSE",
                (payment_id,),
            )
