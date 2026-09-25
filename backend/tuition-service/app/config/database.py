import asyncio
import aiomysql
from app.config.env import settings

_pool: aiomysql.Pool | None = None


async def connect_db(retries: int = 15, delay: int = 2) -> None:
    global _pool
    for attempt in range(1, retries + 1):
        try:
            _pool = await aiomysql.create_pool(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                db=settings.MYSQL_DATABASE,
                autocommit=True,
                minsize=2,
                maxsize=10,
                charset="utf8mb4",
            )
            return
        except Exception as e:
            if attempt == retries:
                raise e
            await asyncio.sleep(delay)


async def close_db() -> None:
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()


def get_pool() -> aiomysql.Pool:
    assert _pool is not None, "Database pool not connected"
    return _pool
