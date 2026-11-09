import aiomysql
from app.core.config import get_pool


async def create_otp(payment_id: int | str, otp_code: str) -> None:
    pid = int(payment_id)
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE otps SET is_used = TRUE WHERE payment_id = %s AND is_used = FALSE",
                    (pid,),
                )
                await cur.execute(
                    "INSERT INTO otps (payment_id, otp_code, expires_at, is_used, attempts) "
                    "VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 5 MINUTE), FALSE, 0)",
                    (pid, otp_code),
                )
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise


async def verify_and_consume_otp(payment_id: int | str, otp_code: str) -> dict:
    pid = int(payment_id)
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT id, otp_code, expires_at, is_used, attempts, "
                    "(expires_at >= NOW()) AS is_valid_time "
                    "FROM otps WHERE payment_id = %s ORDER BY id DESC LIMIT 1 FOR UPDATE",
                    (pid,),
                )
                record = await cur.fetchone()
                if not record:
                    await conn.rollback()
                    return {"status": "NOT_FOUND"}

                if record["attempts"] >= 3:
                    if not record["is_used"]:
                        await cur.execute("UPDATE otps SET is_used = TRUE WHERE id = %s", (record["id"],))
                    await conn.commit()
                    return {"status": "MAX_ATTEMPTS", "attempts": record["attempts"]}

                if record["is_used"]:
                    await conn.commit()
                    return {"status": "ALREADY_USED"}

                if not record["is_valid_time"]:
                    await cur.execute("UPDATE otps SET is_used = TRUE WHERE id = %s AND is_used = FALSE", (record["id"],))
                    await conn.commit()
                    return {"status": "EXPIRED"}

                if record["otp_code"] == otp_code:
                    await cur.execute(
                        "UPDATE otps SET is_used = TRUE "
                        "WHERE id = %s AND is_used = FALSE AND attempts < 3 AND expires_at >= NOW()",
                        (record["id"],),
                    )
                    if cur.rowcount == 0:
                        await conn.rollback()
                        return {"status": "ALREADY_USED"}
                    await conn.commit()
                    return {"status": "SUCCESS"}

                new_attempts = int(record["attempts"]) + 1
                mark_used = new_attempts >= 3
                await cur.execute(
                    "UPDATE otps SET attempts = attempts + 1, is_used = IF(%s, TRUE, is_used) WHERE id = %s",
                    (mark_used, record["id"]),
                )
                await conn.commit()

                if new_attempts >= 3:
                    return {"status": "MAX_ATTEMPTS", "attempts": new_attempts}
                return {
                    "status": "WRONG_CODE",
                    "attempts": new_attempts,
                    "remaining": 3 - new_attempts,
                }
        except Exception:
            await conn.rollback()
            raise


async def is_otp_active(otp_code: str) -> bool:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id FROM otps WHERE otp_code = %s AND is_used = FALSE AND expires_at >= NOW() LIMIT 1",
                (otp_code,),
            )
            return await cur.fetchone() is not None
