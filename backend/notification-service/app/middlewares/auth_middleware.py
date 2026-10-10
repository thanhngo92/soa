from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from app.config.env import settings

_bearer = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    try:
        return jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"code": "TOKEN_EXPIRED", "message": "Token has expired"})
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_TOKEN", "message": "Invalid token"})


async def verify_internal_token(x_internal_token: str = Header(None, alias="X-Internal-Token")):
    if not x_internal_token or x_internal_token != settings.INTERNAL_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN_INTERNAL_ONLY", "message": "Access denied: Internal service operation only."},
        )

