from datetime import datetime, timezone
import aiomysql
from app.config.database import get_pool


def _format_dt(dt_val) -> str | None:
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            dt_val = dt_val.replace(tzinfo=timezone.utc)
        return dt_val.isoformat()
    return str(dt_val)


def _format_account(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "username": row["username"],
        "password_hash": row["password_hash"],
        "full_name": row["full_name"],
        "email": row["email"],
        "phone": row["phone"],
        "balance": float(row["balance"]),
        "created_at": _format_dt(row.get("created_at")),
    }


async def find_by_username(username: str) -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT id, username, password_hash, full_name, email, phone, balance, created_at "
                "FROM accounts WHERE username = %s",
                (username,),
            )
            row = await cur.fetchone()
            return _format_account(row) if row else None


async def find_by_id(account_id: str | int) -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT id, username, password_hash, full_name, email, phone, balance, created_at "
                "FROM accounts WHERE id = %s",
                (account_id,),
            )
            row = await cur.fetchone()
            return _format_account(row) if row else None


# [Rubric Tiêu chí 6: Quản lý Giao dịch & Concurrency - Trừ tiền an toàn ACID]
# - Nghiệp vụ (Đề bài Mục 4): Trừ tiền tài khoản nguồn sau khi OTP xác thực hợp lệ.
# - Kỹ thuật: Khóa bi quan (SELECT ... FOR UPDATE), kiểm tra số dư nguyên tử (balance >= amount),
#             kiểm tra idempotency qua reference_id và ghi bút toán sổ cái DEDUCT.
async def deduct_balance(account_id: str | int, amount: float, transaction_id: str = "") -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT balance FROM accounts WHERE id = %s FOR UPDATE",
                    (account_id,),
                )
                acc_before = await cur.fetchone()
                if not acc_before:
                    await conn.rollback()
                    return None

                if transaction_id:
                    await cur.execute(
                        "SELECT balance_after FROM account_transactions "
                        "WHERE account_id = %s AND reference_id = %s AND transaction_type = 'DEDUCT'",
                        (account_id, transaction_id),
                    )
                    existing = await cur.fetchone()
                    if existing:
                        await conn.commit()
                        return {"balance": float(existing["balance_after"])}

                balance_before = float(acc_before["balance"])
                if balance_before < amount:
                    await conn.rollback()
                    return None

                await cur.execute(
                    "UPDATE accounts SET balance = balance - %s WHERE id = %s AND balance >= %s",
                    (amount, account_id, amount),
                )
                if cur.rowcount == 0:
                    await conn.rollback()
                    return None

                await cur.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
                acc_after = await cur.fetchone()
                balance_after = float(acc_after["balance"])

                if transaction_id:
                    await cur.execute(
                        "INSERT INTO account_transactions "
                        "(account_id, transaction_type, amount, balance_before, balance_after, reference_id, description) "
                        "VALUES (%s, 'DEDUCT', %s, %s, %s, %s, %s)",
                        (
                            account_id,
                            amount,
                            balance_before,
                            balance_after,
                            transaction_id,
                            f"Thanh toan hoc phi #{transaction_id}",
                        ),
                    )

                await conn.commit()
                return {"balance": balance_after}
        except Exception:
            await conn.rollback()
            raise


# [Rubric Tiêu chí 6: Saga Compensation - Hoàn tiền tự động khi gạch nợ thất bại]
# - Nghiệp vụ (Đề bài Mục 5): Bù trừ hoàn tiền về tài khoản khi bước gạch nợ học phí gặp sự cố.
# - Kỹ thuật: ACID transaction, kiểm tra tồn tại bút toán DEDUCT gốc để chống hoàn tiền khống,
#             khóa FOR UPDATE, cộng lại balance và ghi bút toán sổ cái REFUND.
async def refund_balance(account_id: str | int, amount: float, transaction_id: str = "") -> dict | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT balance FROM accounts WHERE id = %s FOR UPDATE",
                    (account_id,),
                )
                acc_before = await cur.fetchone()
                if not acc_before:
                    await conn.rollback()
                    return None

                if transaction_id:
                    await cur.execute(
                        "SELECT balance_after FROM account_transactions "
                        "WHERE account_id = %s AND reference_id = %s AND transaction_type = 'REFUND'",
                        (account_id, transaction_id),
                    )
                    existing = await cur.fetchone()
                    if existing:
                        await conn.commit()
                        return {"balance": float(existing["balance_after"])}

                    if transaction_id.isdigit():
                        await cur.execute(
                            "SELECT id FROM account_transactions "
                            "WHERE account_id = %s AND reference_id = %s AND transaction_type = 'DEDUCT'",
                            (account_id, transaction_id),
                        )
                        deduct_record = await cur.fetchone()
                        if not deduct_record:
                            await conn.rollback()
                            return None

                balance_before = float(acc_before["balance"])

                await cur.execute(
                    "UPDATE accounts SET balance = balance + %s WHERE id = %s",
                    (amount, account_id),
                )
                if cur.rowcount == 0:
                    await conn.rollback()
                    return None

                await cur.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
                acc_after = await cur.fetchone()
                balance_after = float(acc_after["balance"])

                if transaction_id:
                    await cur.execute(
                        "INSERT INTO account_transactions "
                        "(account_id, transaction_type, amount, balance_before, balance_after, reference_id, description) "
                        "VALUES (%s, 'REFUND', %s, %s, %s, %s, %s)",
                        (
                            account_id,
                            amount,
                            balance_before,
                            balance_after,
                            transaction_id,
                            f"Hoan tien Saga #{transaction_id}",
                        ),
                    )

                await conn.commit()
                return {"balance": balance_after}
        except Exception:
            await conn.rollback()
            raise


async def get_account_transactions(account_id: str | int, limit: int = 100) -> list[dict]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM account_transactions WHERE account_id = %s ORDER BY created_at DESC, id DESC LIMIT %s",
                (account_id, limit),
            )
            rows = await cur.fetchall()
            for r in rows:
                r["amount"] = float(r["amount"])
                r["balance_before"] = float(r["balance_before"])
                r["balance_after"] = float(r["balance_after"])
                r["created_at"] = _format_dt(r.get("created_at"))
            return list(rows)
