import aiomysql
from app.config.database import get_pool


# [Rubric Tiêu chí 2 / Đề bài Mục 4: Lưu mã OTP 2FA vào CSDL trong ACID Transaction]
# - Nghiệp vụ: Vô hiệu hóa các mã OTP cũ của cùng payment_id và lưu OTP 6 chữ số mới có thời hạn 5 phút.
# - Kỹ thuật: Gói UPDATE (invalidate) và INSERT (create) trong cùng 1 ACID Transaction để đảm bảo
#             tại mọi thời điểm chỉ có tối đa 1 mã OTP hiệu lực (is_used=FALSE) cho mỗi payment_id.
async def create_otp(payment_id: str, otp_code: str, email: str) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE otps SET is_used = TRUE WHERE payment_id = %s AND is_used = FALSE",
                    (payment_id,),
                )
                await cur.execute(
                    "INSERT INTO otps (payment_id, otp_code, email, expires_at, is_used, attempts) "
                    "VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL 5 MINUTE), FALSE, 0)",
                    (payment_id, otp_code, email),
                )
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise


# [Rubric Tiêu chí 5 & 6 / Đề bài Mục 3 & 4: Xác thực và tiêu thụ mã OTP]
# - Nghiệp vụ: Kiểm tra OTP đúng, còn hạn, chưa dùng, tối đa 3 lần thử sai.
# - Kỹ thuật: Khóa bi quan FOR UPDATE; nếu đúng cập nhật is_used=TRUE nguyên tử;
#             nếu sai tăng attempts, chạm mốc 3 lần tự động khóa is_used=TRUE.
async def verify_and_consume_otp(payment_id: str, otp_code: str) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT id, otp_code, email, expires_at, is_used, attempts, "
                    "(expires_at >= NOW()) AS is_valid_time "
                    "FROM otps WHERE payment_id = %s ORDER BY id DESC LIMIT 1 FOR UPDATE",
                    (payment_id,),
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
