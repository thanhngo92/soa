from fastapi import Header, HTTPException, status
from app.config.env import settings


async def verify_internal_token(x_internal_token: str = Header(None, alias="X-Internal-Token")):
    if not x_internal_token or x_internal_token != settings.INTERNAL_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN_INTERNAL_ONLY", "message": "Access denied: Internal service operation only."},
        )
