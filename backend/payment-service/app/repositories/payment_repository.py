import aiomysql
from app.config.database import get_pool


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
    """Atomic state transition in payment workflow state machine.
    Enforces valid state transition from `from_status` to `to_status`.
    Returns True if transitioned successfully, False if condition was not met (preventing race conditions).
    """
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
                "SELECT * FROM payments WHERE account_id = %s ORDER BY created_at DESC LIMIT 100",
                (account_id,),
            )
            rows = await cur.fetchall()
            for r in rows:
                r["amount"] = float(r["amount"])
            return list(rows)
