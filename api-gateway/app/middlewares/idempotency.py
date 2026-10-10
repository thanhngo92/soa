import asyncio
import time
from typing import Tuple


class IdempotencyPayloadMismatch(Exception):
    """Raised when an Idempotency-Key is reused with a different request payload."""
    pass


class IdempotencyRecord:
    def __init__(self, status: str = "IN_PROGRESS", body_hash: str = ""):
        self.status = status  # "IN_PROGRESS" or "COMPLETED"
        self.body_hash: str = body_hash
        self.response_content: bytes = b""
        self.status_code: int = 200
        self.media_type: str = "application/json"
        self.created_at: float = time.time()
        self.event: asyncio.Event = asyncio.Event()


class IdempotencyStore:
    """
    In-memory Idempotency Store with TTL support, user-scoping, and payload verification.
    Protects downstream services from duplicate requests with the same Idempotency-Key.
    """

    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._store: dict[str, IdempotencyRecord] = {}
        self._lock = asyncio.Lock()

    def _cleanup_expired(self):
        now = time.time()
        expired_keys = [k for k, v in self._store.items() if now - v.created_at > self.ttl]
        for k in expired_keys:
            del self._store[k]

    async def get_or_create(self, key: str, body_hash: str = "") -> Tuple[IdempotencyRecord, bool]:
        """
        Returns (record, is_new).
        If is_new is True, the record is newly created with status 'IN_PROGRESS'.
        Raises IdempotencyPayloadMismatch if payload differs from previous request with same key.
        """
        async with self._lock:
            self._cleanup_expired()
            record = self._store.get(key)
            if record is None:
                new_record = IdempotencyRecord(status="IN_PROGRESS", body_hash=body_hash)
                self._store[key] = new_record
                return new_record, True

            if record.body_hash and body_hash and record.body_hash != body_hash:
                raise IdempotencyPayloadMismatch("Payload does not match original request with this Idempotency-Key")

            return record, False

    async def save_completed(self, key: str, status_code: int, content: bytes, media_type: str):
        async with self._lock:
            record = self._store.get(key)
            if record:
                record.status = "COMPLETED"
                record.status_code = status_code
                record.response_content = content
                record.media_type = media_type
                record.event.set()

    async def remove(self, key: str):
        async with self._lock:
            record = self._store.pop(key, None)
            if record:
                record.event.set()


# Global in-memory instance with 5-minute TTL
idempotency_store = IdempotencyStore(ttl_seconds=300)
