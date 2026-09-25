from datetime import datetime
import aiomysql
from app.config.database import get_pool


async def create_payment(data: dict) -> str:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO payments (account_id, email, student_id, student_name, amount, status) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    data["account_id"],
                    data["email"],
                    data["student_id"],
                    data["student_name"],
                    data["amount"],
                    data.get("status", "PENDING"),
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
            row["_id"] = str(row["id"])
            row["amount"] = float(row["amount"])
            return row


async def update_status(payment_id: str, status: str, error_code: str | None = None) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            if error_code:
                await cur.execute(
                    "UPDATE payments SET status = %s, completed_at = NOW(), error_code = %s WHERE id = %s",
                    (status, error_code, payment_id),
                )
            else:
                await cur.execute(
                    "UPDATE payments SET status = %s, completed_at = NOW() WHERE id = %s",
                    (status, payment_id),
                )


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
                r["_id"] = str(r["id"])
                r["amount"] = float(r["amount"])
            return list(rows)
