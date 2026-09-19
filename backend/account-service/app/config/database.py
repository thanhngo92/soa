from motor.motor_asyncio import AsyncIOMotorClient
from app.config.env import settings

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.MONGO_URI)


async def close_db() -> None:
    global _client
    if _client:
        _client.close()


def get_db():
    assert _client is not None, "Database not connected"
    return _client[settings.DATABASE_NAME]
