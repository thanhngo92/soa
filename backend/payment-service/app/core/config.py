import asyncio
import aiomysql
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "payment-service"
    PORT: int = 8815

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 8552
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "rootpassword"
    MYSQL_DATABASE: str = "payment_db"

    JWT_SECRET: str = "super_secret_jwt_key_change_in_prod"
    INTERNAL_SERVICE_KEY: str = "super_internal_service_secret_key_2026"
    ACCOUNT_SERVICE_URL: str = "http://account-service:8661"
    TUITION_SERVICE_URL: str = "http://tuition-service:8732"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8940"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

_pool: aiomysql.Pool | None = None


async def connect_db(retries: int = 45, delay: int = 2) -> None:
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
                pool_recycle=3600,
                connect_timeout=10,
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
