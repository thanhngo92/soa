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


async def verify_and_consume_otp(payment_id: str, otp_code: str) -> dict | None:
    """Xac thuc va danh dau da su dung ma OTP trong 1 thao tac nguyen tu."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Danh dau da dung neu ma hop le, con han va chua qua 5 lan thu sai
            await cur.execute(
                "UPDATE otps SET is_used = TRUE "
                "WHERE payment_id = %s AND otp_code = %s AND is_used = FALSE AND expires_at >= NOW() AND attempts < 5",
                (payment_id, otp_code),
            )
            if cur.rowcount > 0:
                await cur.execute(
                    "SELECT * FROM otps WHERE payment_id = %s AND otp_code = %s ORDER BY id DESC LIMIT 1",
                    (payment_id, otp_code),
                )
                return await cur.fetchone()

            # Ghi nhan lan thu sai va khoa neu qua 5 lan
            await cur.execute(
                "UPDATE otps SET attempts = attempts + 1 WHERE payment_id = %s AND is_used = FALSE",
                (payment_id,),
            )
            await cur.execute(
                "UPDATE otps SET is_used = TRUE WHERE payment_id = %s AND attempts >= 5",
                (payment_id,),
            )
            return None


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
