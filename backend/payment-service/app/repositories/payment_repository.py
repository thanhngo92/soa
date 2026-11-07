import aiomysql
from app.config.database import get_pool


async def supersede_pending_payments(account_id: str, student_id: str) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE payments SET status = 'FAILED', error_code = 'SUPERSEDED', completed_at = NOW() "
                "WHERE account_id = %s AND student_id = %s AND status = 'PENDING'",
                (account_id, student_id),
            )


async def create_payment(data: dict) -> str:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO payments (account_id, email, student_id, student_name, amount, status, semester) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    data["account_id"],
                    data["email"],
                    data["student_id"],
                    data["student_name"],
                    data["amount"],
                    data.get("status", "PENDING"),
                    data.get("semester"),
                ),
            )
            return str(cur.lastrowid)


async def find_by_id(payment_id: str) -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
            row = await cur.fetchone()
            if not row:
                return None
            row["amount"] = float(row["amount"])
            return row


async def transition_status(
    payment_id: str,
    from_status: str,
    to_status: str,
    error_code: str | None = None,
) -> bool:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            if to_status in ("SUCCESS", "FAILED"):
                await cur.execute(
                    "UPDATE payments SET status = %s, completed_at = NOW(), error_code = %s WHERE id = %s AND status = %s",
                    (to_status, error_code, payment_id, from_status),
                )
            else:
                await cur.execute(
                    "UPDATE payments SET status = %s, error_code = %s WHERE id = %s AND status = %s",
                    (to_status, error_code, payment_id, from_status),
                )
            return cur.rowcount > 0


async def find_by_account(account_id: str) -> list[dict]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "UPDATE payments SET status = 'FAILED', error_code = 'OTP_EXPIRED', completed_at = NOW() "
                "WHERE account_id = %s AND status = 'PENDING' AND created_at < DATE_SUB(NOW(), INTERVAL 5 MINUTE)",
                (account_id,),
            )
            await cur.execute(
                "SELECT * FROM payments WHERE account_id = %s ORDER BY created_at DESC, id DESC LIMIT 100",
                (account_id,),
            )
            rows = await cur.fetchall()
            for r in rows:
                r["amount"] = float(r["amount"])
            return list(rows)
