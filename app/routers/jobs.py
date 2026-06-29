from fastapi import HTTPException, Depends, status, APIRouter
from pymongo import ReturnDocument
from app.db import job_collection
from app.schemas.schemas import JobUpdate, JobModel, JobCollection, ObjectId, JobCreate
from datetime import datetime, timezone
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from app.utils import build_dedup_key
from app.auth import get_api_key


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(get_api_key)],
)


@router.post(
        "/jobs",
        response_description= "Add new job",
        response_model=JobModel,
        status_code=status.HTTP_201_CREATED,
        response_model_by_alias=True
        )
async def create_job(job: JobCreate, api_key: str = Depends(get_api_key)):
    new_job = job.model_dump(mode="json")
    new_job["dedup_key"] = build_dedup_key(job.source, str(job.link))
    new_job["scraped_at"] = datetime.now(timezone.utc)

    try:
        result = await job_collection.insert_one(new_job)
    except DuplicateKeyError:
        existing = await job_collection.find_one({"dedup_key": new_job["dedup_key"]})
        return existing
    return await job_collection.find_one({"_id": result.inserted_id})

@router.get(
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

@router.get(
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

@router.put(
    "/jobs/{id}",
    response_description="Update a job",
    response_model=JobModel,
    response_model_by_alias=True
)
async def update_job(id: str, job: JobUpdate, api_key: str = Depends(get_api_key)):
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

@router.delete("/jobs/{id}", response_description="Delete a job", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(id: str, api_key: str = Depends(get_api_key)):
    try:
        object_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job id")
    delete_result = await job_collection.delete_one({"_id": object_id})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {id} not found")
