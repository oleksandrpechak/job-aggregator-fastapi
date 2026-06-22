from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import settings
import secrets

api_key_header = APIKeyHeader(
    name="x-api-key",
    auto_error=False,
)

def get_api_key(
    api_key: str = Security(api_key_header),
):
    if api_key and secrets.compare_digest(api_key, settings.api_key):
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )