from fastapi import HTTPException, APIRouter, Depends
from app.auth import get_api_key
from app.db import client
from app.redis_client import redis_client
import logging


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/health",
    tags=["health"],
    dependencies=[Depends(get_api_key)],
)

@router.get("/health")
async def check_health():
    await client.admin.command("ping")
    return {
        "status": "ok",
        "mongodb": "working"
    }

@router.get("/redis-health")
async def redis_health():
    try:
        await redis_client.ping()
        return {"redis": "ok"}
    except Exception as e:
        raise HTTPException(500, f"Redis error: {str(e)}")
