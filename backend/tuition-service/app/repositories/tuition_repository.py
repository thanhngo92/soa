import aiomysql
from app.config.database import get_pool


async def find_by_mssv(mssv: str) -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT t.id, s.student_id, s.student_name, s.major, t.semester, "
                "t.amount, t.status, t.paid_at, t.created_at "
                "FROM students s "
                "INNER JOIN tuitions t ON s.student_id = t.student_id "
                "WHERE s.student_id = %s "
                "ORDER BY CASE WHEN t.status = 'UNPAID' THEN 0 ELSE 1 END, t.id ASC LIMIT 1",
                (mssv,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            row["amount"] = float(row["amount"])
            return row


async def find_by_id(tuition_id: int) -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT t.id, s.student_id, s.student_name, s.major, t.semester, "
                "t.amount, t.status, t.paid_at, t.created_at "
                "FROM tuitions t "
                "INNER JOIN students s ON s.student_id = t.student_id "
                "WHERE t.id = %s",
                (tuition_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            row["amount"] = float(row["amount"])
            return row


async def mark_paid(
    tuition_id: int | None = None,
    mssv: str | None = None,
    semester: str | None = None,
    expected_amount: float | None = None,
) -> dict | None:
    """Atomic UNPAID -> PAID inside an ACID transaction with SELECT ... FOR UPDATE row lock.
    Verifies UNPAID status and exact tuition amount before marking PAID.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if tuition_id is not None:
                    await cur.execute(
                        "SELECT id, amount, status FROM tuitions WHERE id = %s FOR UPDATE",
                        (tuition_id,),
                    )
                elif semester:
                    await cur.execute(
                        "SELECT id, amount, status FROM tuitions "
                        "WHERE student_id = %s AND semester = %s FOR UPDATE",
                        (mssv, semester),
                    )
                else:
                    await cur.execute(
                        "SELECT id, amount, status FROM tuitions "
                        "WHERE student_id = %s "
                        "ORDER BY CASE WHEN status = 'UNPAID' THEN 0 ELSE 1 END, id ASC LIMIT 1 FOR UPDATE",
                        (mssv,),
                    )

                target = await cur.fetchone()
                if not target or target["status"] != "UNPAID":
                    await conn.rollback()
                    return None

                if expected_amount is not None and abs(float(target["amount"]) - float(expected_amount)) > 0.01:
                    await conn.rollback()
                    return None

                await cur.execute(
                    "UPDATE tuitions SET status = 'PAID', paid_at = NOW() "
                    "WHERE id = %s AND status = 'UNPAID'",
                    (target["id"],),
                )
                if cur.rowcount == 0:
                    await conn.rollback()
                    return None

                await cur.execute(
                    "SELECT t.id, s.student_id, s.student_name, s.major, t.semester, "
                    "t.amount, t.status, t.paid_at "
                    "FROM tuitions t "
                    "INNER JOIN students s ON s.student_id = t.student_id "
                    "WHERE t.id = %s",
                    (target["id"],),
                )
                row = await cur.fetchone()
                await conn.commit()
                if row:
                    row["amount"] = float(row["amount"])
                return row
        except Exception:
            await conn.rollback()
            raise
