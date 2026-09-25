import aiomysql
from app.config.database import get_pool


async def find_by_mssv(mssv: str) -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM tuitions WHERE student_id = %s", (mssv,))
            row = await cur.fetchone()
            if not row:
                return None
            row["amount"] = float(row["amount"])
            return row


async def mark_paid(mssv: str, paid_by: str, transaction_id: str) -> dict | None:
    """Atomic UNPAID -> PAID. Returns None if already paid (Concurrency guard via MySQL row lock)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "UPDATE tuitions SET status = 'PAID', paid_at = NOW(), paid_by = %s, transaction_id = %s "
                "WHERE student_id = %s AND status = 'UNPAID'",
                (paid_by, transaction_id, mssv),
            )
            if cur.rowcount == 0:
                return None
            await cur.execute("SELECT * FROM tuitions WHERE student_id = %s", (mssv,))
            row = await cur.fetchone()
            if row:
                row["amount"] = float(row["amount"])
            return row


async def revert_paid(mssv: str, transaction_id: str) -> dict | None:
    """Compensating transaction: PAID -> UNPAID (only if same transaction_id)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "UPDATE tuitions SET status = 'UNPAID', paid_at = NULL, paid_by = NULL, transaction_id = NULL "
                "WHERE student_id = %s AND status = 'PAID' AND transaction_id = %s",
                (mssv, transaction_id),
            )
            if cur.rowcount == 0:
                return None
            await cur.execute("SELECT * FROM tuitions WHERE student_id = %s", (mssv,))
            row = await cur.fetchone()
            if row:
                row["amount"] = float(row["amount"])
            return row
