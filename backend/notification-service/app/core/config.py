import asyncio
import aiomysql
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "notification-service"
    PORT: int = 8940

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 8552
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "rootpassword"
    MYSQL_DATABASE: str = "notification_db"

    INTERNAL_SERVICE_KEY: str = "super_internal_service_secret_key_2026"

    # SMTP Configuration
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = False
    MAIL_FROM: str = "noreply@ibanking.local"

    @property
    def is_real_smtp(self) -> bool:
        """Kiểm tra có cấu hình SMTP thật hay không (có user, password và host không phải mailpit)."""
        return bool(
            self.SMTP_USER
            and self.SMTP_PASSWORD
            and self.SMTP_HOST
            and self.SMTP_HOST.lower() != "mailpit"
        )

    @field_validator("SMTP_HOST", mode="before")
    @classmethod
    def validate_smtp_host(cls, v):
        if v is None:
            return "mailpit"
        val = str(v).strip()
        if not val or val.lower() in ("none", "null"):
            return "mailpit"
        return val

    @field_validator("SMTP_PORT", mode="before")
    @classmethod
    def validate_smtp_port(cls, v):
        if v is None:
            return 1025
        val = str(v).strip()
        if not val or val.lower() in ("none", "null"):
            return 1025
        return int(val)

    @field_validator("SMTP_USE_TLS", mode="before")
    @classmethod
    def validate_smtp_tls(cls, v):
        if v is None:
            return False
        val = str(v).strip().lower()
        if val in ("true", "1", "yes"):
            return True
        return False

    @field_validator("SMTP_USER", "SMTP_PASSWORD", mode="before")
    @classmethod
    def validate_credentials(cls, v):
        if v is None:
            return None
        val = str(v).strip()
        if not val or val.lower() in ("none", "null", "undefined"):
            return None
        return val

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
