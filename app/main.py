from fastapi import FastAPI, Depends
from pymongo import ASCENDING
from contextlib import asynccontextmanager
from app.db import client, job_collection, alerts_sent_collection
from app.routers.filters import router as filters_router
from app.routers.jobs import router as jobs_router
from app.routers.health import router as health_router
from app.tasks import ingest_dou
from app.auth import get_api_key
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup: creating indexes")
    await job_collection.create_index(
        [("dedup_key", ASCENDING)],
        unique=True
    )
    await alerts_sent_collection.create_index(
        [("job_id", ASCENDING), ("filter_id", ASCENDING)],
        unique=True,
        name="uniq_alert_job_filter",
    )
    logger.info("startup: indexes created")

    yield
    logger.info("shutdown: closing database connections")
    client.close()

app = FastAPI(lifespan=lifespan)

app.include_router(filters_router)
app.include_router(health_router)
app.include_router(jobs_router)