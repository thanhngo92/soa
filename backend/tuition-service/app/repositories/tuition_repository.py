import aiomysql
from app.config.database import get_pool


async def find_by_mssv(mssv: str) -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM tuitions WHERE student_id = %s "
                "ORDER BY CASE WHEN status = 'UNPAID' THEN 0 ELSE 1 END, id ASC LIMIT 1",
                (mssv,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            row["amount"] = float(row["amount"])
            return row


async def mark_paid(mssv: str, paid_by: str, transaction_id: str, semester: str | None = None) -> dict | None:
    """Atomic UNPAID -> PAID. Returns None if already paid (Concurrency guard via MySQL row lock).
    Supports semester filtering to ensure only targeted semester is marked PAID.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            if semester:
                await cur.execute(
                    "UPDATE tuitions SET status = 'PAID', paid_at = NOW(), paid_by = %s, transaction_id = %s "
                    "WHERE student_id = %s AND semester = %s AND status = 'UNPAID'",
                    (paid_by, transaction_id, mssv, semester),
                )
            else:
                # Update only one unpaid tuition record safely
                await cur.execute(
                    "UPDATE tuitions SET status = 'PAID', paid_at = NOW(), paid_by = %s, transaction_id = %s "
                    "WHERE id = (SELECT id FROM (SELECT id FROM tuitions WHERE student_id = %s AND status = 'UNPAID' ORDER BY id ASC LIMIT 1) AS t)",
                    (paid_by, transaction_id, mssv),
                )
            if cur.rowcount == 0:
                return None
            if semester:
                await cur.execute("SELECT * FROM tuitions WHERE student_id = %s AND semester = %s", (mssv, semester))
            else:
                await cur.execute("SELECT * FROM tuitions WHERE student_id = %s AND transaction_id = %s", (mssv, transaction_id))
            row = await cur.fetchone()
            if row:
                row["amount"] = float(row["amount"])
            return row


async def revert_paid(mssv: str, transaction_id: str | None = None, semester: str | None = None) -> dict | None:
    """Compensating transaction: PAID -> UNPAID (supports specific txn, semester or admin reset)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            if transaction_id:
                await cur.execute(
                    "UPDATE tuitions SET status = 'UNPAID', paid_at = NULL, paid_by = NULL, transaction_id = NULL "
                    "WHERE student_id = %s AND status = 'PAID' AND transaction_id = %s",
                    (mssv, transaction_id),
                )
            elif semester:
                await cur.execute(
                    "UPDATE tuitions SET status = 'UNPAID', paid_at = NULL, paid_by = NULL, transaction_id = NULL "
                    "WHERE student_id = %s AND status = 'PAID' AND semester = %s",
                    (mssv, semester),
                )
            else:
                await cur.execute(
                    "UPDATE tuitions SET status = 'UNPAID', paid_at = NULL, paid_by = NULL, transaction_id = NULL "
                    "WHERE student_id = %s AND status = 'PAID'",
                    (mssv,),
                )
            if cur.rowcount == 0:
                return None
            await cur.execute("SELECT * FROM tuitions WHERE student_id = %s ORDER BY id DESC LIMIT 1", (mssv,))
            row = await cur.fetchone()
            if row:
                row["amount"] = float(row["amount"])
            return row
