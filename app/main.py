from fastapi import FastAPI, HTTPException
from pymongo import ReturnDocument, ASCENDING
from contextlib import asynccontextmanager
from app.db import client, job_collection
from app.schemas import JobUpdate, JobModel, JobCollection, ObjectId, JobCreate
from fastapi import status
from datetime import datetime, timezone
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from app.redis_client import redis_client
from app.utils import build_dedup_key
from app.tasks import ingest_dou_jobs
import logging


logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    await job_collection.create_index(
        [("dedup_key", ASCENDING)],
        unique=True
    )
    logger.info("Indexes created")

    yield 
    logger.info("Shutting down")
    client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def check_health():
    await client.admin.command("ping")
    return {
        "status": "ok",
        "mongodb": "working"
    }

@app.get("/redis-health")
async def redis_health():
    try:
        await redis_client.ping()
        return {"redis": "ok"}
    except Exception as e:
        raise HTTPException(500, f"Redis error: {str(e)}")

@app.post(
        "/jobs",
        response_description= "Add new job",
        response_model=JobModel,
        status_code=status.HTTP_201_CREATED,
        response_model_by_alias=True
        )
async def create_job(job: JobCreate):
    new_job = job.model_dump(mode="json")
    new_job["dedup_key"] = build_dedup_key(job.source, str(job.link))
    new_job["scraped_at"] = datetime.now(timezone.utc)

    try:
        result = await job_collection.insert_one(new_job)
    except DuplicateKeyError:
        existing = await job_collection.find_one({"dedup_key": new_job["dedup_key"]})
        return existing
    return await job_collection.find_one({"_id": result.inserted_id})

@app.get(
    "/jobs/",
    response_description="List all jobs",
    response_model=JobCollection,
    response_model_by_alias=True
)
async def list_jobs(skip: int = 0, limit: int = 20):
    jobs = await (
        job_collection.find().skip(skip).limit(limit).to_list(limit)
        )
    return JobCollection(jobs=jobs)

@app.get(
    "/jobs/{id}",
    response_description="Get a single job",
    response_model=JobModel,
    response_model_by_alias=True
)
async def show_job(id:str):
    try:
        object_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")
    if (job := await job_collection.find_one({"_id": object_id})) is not None:
        return job
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {id} not found")

@app.put(
    "/jobs/{id}",
    response_description="Update a job",
    response_model=JobModel,
    response_model_by_alias=True
)
async def update_job(id: str, job: JobUpdate):
    try:
        object_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")
    update_data = job.model_dump(mode="json", exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    update_result = await job_collection.find_one_and_update(
        {"_id": object_id},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
    )
    if not update_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {id} not found"
        )
    return update_result

@app.delete("/jobs/{id}", response_description="Delete a job", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(id: str):
    try:
        object_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")
    delete_result = await job_collection.delete_one({"_id": object_id})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {id} not found")




@app.post("/scrape/dou")
async def scrape_dou():
    task = ingest_dou_jobs.delay()

    return {
        "task_id": task.id,
        "status": "queued"
    }