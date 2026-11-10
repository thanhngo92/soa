from datetime import datetime, timezone
import aiomysql
from app.core.config import get_pool


async def find_all_by_mssv(mssv: str) -> list[dict]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT t.id, s.student_id, s.student_name, s.major, t.semester, "
                "t.amount, t.status, t.paid_at, t.created_at "
                "FROM students s "
                "INNER JOIN tuitions t ON s.student_id = t.student_id "
                "WHERE s.student_id = %s "
                "ORDER BY CASE WHEN t.status = 'UNPAID' THEN 0 ELSE 1 END, t.id ASC",
                (mssv,),
            )
            rows = await cur.fetchall()
            for row in rows:
                row["amount"] = float(row["amount"])
            return rows


async def find_by_mssv(mssv: str) -> dict | None:
    rows = await find_all_by_mssv(mssv)
    return rows[0] if rows else None


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
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                target_student_id = mssv
                if not target_student_id and tuition_id is not None:
                    await cur.execute("SELECT student_id FROM tuitions WHERE id = %s", (tuition_id,))
                    t_row = await cur.fetchone()
                    if t_row:
                        target_student_id = t_row["student_id"]

                if not target_student_id:
                    await conn.rollback()
                    return None

                # [Quy định: Không thanh toán từng phần - Thanh toán 1 lượt toàn bộ học phí nợ]
                # Khóa bi quan FOR UPDATE toàn bộ các khoản nợ UNPAID của sinh viên
                await cur.execute(
                    "SELECT id, semester, amount, status FROM tuitions "
                    "WHERE student_id = %s AND status = 'UNPAID' FOR UPDATE",
                    (target_student_id,),
                )
                unpaid_rows = await cur.fetchall()
                if not unpaid_rows:
                    await conn.rollback()
                    return None

                total_amount = sum(float(r["amount"]) for r in unpaid_rows)
                if expected_amount is not None and abs(total_amount - float(expected_amount)) > 0.01:
                    await conn.rollback()
                    return None

                ids = [r["id"] for r in unpaid_rows]
                ids_format = ",".join(["%s"] * len(ids))
                await cur.execute(
                    f"UPDATE tuitions SET status = 'PAID', paid_at = NOW() "
                    f"WHERE id IN ({ids_format}) AND status = 'UNPAID'",
                    ids,
                )
                if cur.rowcount != len(ids):
                    await conn.rollback()
                    return None

                await cur.execute(
                    "SELECT student_id, student_name, major FROM students WHERE student_id = %s",
                    (target_student_id,),
                )
                student = await cur.fetchone()
                await conn.commit()

                semesters_str = ", ".join(r["semester"] for r in unpaid_rows)
                now_str = datetime.now(timezone.utc).isoformat()
                return {
                    "id": ids[0],
                    "tuition_id": ids[0],
                    "tuition_ids": ids,
                    "student_id": target_student_id,
                    "student_name": student["student_name"] if student else "",
                    "semester": semesters_str,
                    "amount": total_amount,
                    "status": "PAID",
                    "paid_at": now_str,
                }
        except Exception:
            await conn.rollback()
            raise
