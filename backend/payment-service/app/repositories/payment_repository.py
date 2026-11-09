import aiomysql
from app.config.database import get_pool


async def create_payment(data: dict) -> str:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO payments (account_id, tuition_id, amount, status) "
                "VALUES (%s, %s, %s, %s)",
                (
                    int(data["account_id"]),
                    int(data["tuition_id"]),
                    data["amount"],
                    data.get("status", "PENDING"),
                ),
            )
            return str(cur.lastrowid)


async def find_by_id(payment_id: str | int) -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM payments WHERE id = %s", (int(payment_id),))
            row = await cur.fetchone()
            if not row:
                return None
            row["amount"] = float(row["amount"])
            return row


async def verify_otp_and_lock_processing(
    payment_id: str | int,
    user_id: str | int,
    otp_code: str,
    verify_otp_fn,
) -> dict:
    """Locks the payment row with SELECT ... FOR UPDATE while verifying OTP and transitioning to PROCESSING.
    Prevents concurrent confirm requests on the same payment_id from racing OTP attempts or double execution.
    """
    pid = int(payment_id)
    uid = int(user_id)
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM payments WHERE id = %s FOR UPDATE", (pid,))
                payment = await cur.fetchone()
                if not payment:
                    await conn.rollback()
                    return {"status": "NOT_FOUND"}

                if int(payment["account_id"]) != uid:
                    await conn.rollback()
                    return {"status": "FORBIDDEN"}

                if payment["status"] != "PENDING":
                    await conn.rollback()
                    return {"status": "NOT_PENDING", "current_status": payment["status"]}

                otp_res = await verify_otp_fn(str(pid), otp_code)
                if not otp_res.get("success"):
                    err_code = otp_res.get("code", "INVALID_OTP")
                    if err_code in ("OTP_MAX_ATTEMPTS_EXCEEDED", "OTP_EXPIRED"):
                        await cur.execute(
                            "UPDATE payments SET status = 'FAILED', completed_at = NOW(), error_code = %s "
                            "WHERE id = %s AND status = 'PENDING'",
                            (err_code, pid),
                        )
                    await conn.commit()
                    return {
                        "status": "OTP_FAILED",
                        "code": err_code,
                        "message": otp_res.get("message", "Mã OTP không chính xác, đã hết hạn hoặc quá số lần thử."),
                    }

                await cur.execute(
                    "UPDATE payments SET status = 'PROCESSING', error_code = NULL "
                    "WHERE id = %s AND status = 'PENDING'",
                    (pid,),
                )
                if cur.rowcount == 0:
                    await conn.rollback()
                    return {"status": "NOT_PENDING"}

                await conn.commit()
                payment["amount"] = float(payment["amount"])
                return {"status": "OK", "payment": payment}
        except Exception:
            await conn.rollback()
            raise


async def transition_status(
    payment_id: str | int,
    from_status: str,
    to_status: str,
    error_code: str | None = None,
) -> bool:
    pid = int(payment_id)
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            if to_status in ("SUCCESS", "FAILED"):
                await cur.execute(
                    "UPDATE payments SET status = %s, completed_at = NOW(), error_code = %s WHERE id = %s AND status = %s",
                    (to_status, error_code, pid, from_status),
                )
            else:
                await cur.execute(
                    "UPDATE payments SET status = %s, error_code = %s WHERE id = %s AND status = %s",
                    (to_status, error_code, pid, from_status),
                )
            return cur.rowcount > 0


async def find_by_account(account_id: str | int) -> list[dict]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM payments WHERE account_id = %s AND status IN ('SUCCESS', 'FAILED') ORDER BY id DESC LIMIT 100",
                (int(account_id),),
            )
            rows = await cur.fetchall()
            for r in rows:
                r["amount"] = float(r["amount"])
            return list(rows)
