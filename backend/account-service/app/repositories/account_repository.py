import aiomysql
from app.config.database import get_pool


def _format_account(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "_id": str(row["id"]),
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


async def deduct_balance(account_id: str | int, amount: float) -> dict | None:
    """Atomic deduction in MySQL (InnoDB row-level lock).
    UPDATE condition ensures balance >= amount. Returns new balance or None.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "UPDATE accounts SET balance = balance - %s WHERE id = %s AND balance >= %s",
                (amount, account_id, amount),
            )
            if cur.rowcount == 0:
                return None
            await cur.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
            row = await cur.fetchone()
            if not row:
                return None
            return {"balance": float(row["balance"])}


async def refund_balance(account_id: str | int, amount: float) -> dict | None:
    """Compensating transaction — adds amount back to balance."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "UPDATE accounts SET balance = balance + %s WHERE id = %s",
                (amount, account_id),
            )
            if cur.rowcount == 0:
                return None
            await cur.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
            row = await cur.fetchone()
            if not row:
                return None
            return {"balance": float(row["balance"])}
