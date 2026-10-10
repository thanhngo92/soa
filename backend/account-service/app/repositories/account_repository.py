import aiomysql
from app.config.database import get_pool


def _format_account(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "username": row["username"],
        "password_hash": row["password_hash"],
        "full_name": row["full_name"],
        "email": row["email"],
        "phone": row["phone"],
        "balance": float(row["balance"]),
        "created_at": row.get("created_at"),
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


async def deduct_balance(account_id: str | int, amount: float, transaction_id: str = "") -> dict | None:
    """Tru so du tai khoan va ghi nhan bien dong so du vao so cai."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Kiem tra idempotency neu da thuc hien truoc do
            if transaction_id:
                await cur.execute(
                    "SELECT balance_after FROM account_transactions "
                    "WHERE account_id = %s AND reference_id = %s AND transaction_type = 'DEDUCT'",
                    (account_id, transaction_id),
                )
                existing = await cur.fetchone()
                if existing:
                    return {"balance": float(existing["balance_after"])}

            # Tru so du (yeu cau so du >= so tien can tru)
            await cur.execute(
                "UPDATE accounts SET balance = balance - %s WHERE id = %s AND balance >= %s",
                (amount, account_id, amount),
            )
            if cur.rowcount == 0:
                return None

            # Lay so du moi nhat sau khi cap nhat
            await cur.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
            acc = await cur.fetchone()
            balance_after = float(acc["balance"])
            balance_before = balance_after + amount

            # Ghi nhat ky so cai
            if transaction_id:
                await cur.execute(
                    "INSERT INTO account_transactions (account_id, transaction_type, amount, balance_before, balance_after, reference_id, description) "
                    "VALUES (%s, 'DEDUCT', %s, %s, %s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE id=id",
                    (account_id, amount, balance_before, balance_after, transaction_id, f"Thanh toan hoc phi #{transaction_id}"),
                )
            return {"balance": balance_after}


async def refund_balance(account_id: str | int, amount: float, transaction_id: str = "") -> dict | None:
    """Hoan lai so du tai khoan va ghi nhan giao dich bu tru."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Kiem tra idempotency neu da hoan tien truoc do
            if transaction_id:
                await cur.execute(
                    "SELECT balance_after FROM account_transactions "
                    "WHERE account_id = %s AND reference_id = %s AND transaction_type = 'REFUND'",
                    (account_id, transaction_id),
                )
                existing = await cur.fetchone()
                if existing:
                    return {"balance": float(existing["balance_after"])}

            await cur.execute(
                "UPDATE accounts SET balance = balance + %s WHERE id = %s",
                (amount, account_id),
            )
            if cur.rowcount == 0:
                return None

            await cur.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
            acc = await cur.fetchone()
            balance_after = float(acc["balance"])
            balance_before = balance_after - amount

            # Ghi nhat ky hoan tien
            if transaction_id:
                await cur.execute(
                    "INSERT INTO account_transactions (account_id, transaction_type, amount, balance_before, balance_after, reference_id, description) "
                    "VALUES (%s, 'REFUND', %s, %s, %s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE id=id",
                    (account_id, amount, balance_before, balance_after, transaction_id, f"Hoan tien Saga #{transaction_id}"),
                )
            return {"balance": balance_after}


async def get_account_transactions(account_id: str | int, limit: int = 100) -> list[dict]:
    """Lay danh sach bien dong so du tu so cai account_transactions."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM account_transactions WHERE account_id = %s ORDER BY created_at DESC LIMIT %s",
                (account_id, limit),
            )
            rows = await cur.fetchall()
            for r in rows:
                r["amount"] = float(r["amount"])
                r["balance_before"] = float(r["balance_before"])
                r["balance_after"] = float(r["balance_after"])
            return list(rows)
