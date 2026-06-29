from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import ReturnDocument
from app.db import filter_collection
from app.schemas.filter import FilterCreate, FilterUpdate, FilterModel
from app.auth import get_api_key


router = APIRouter(
    prefix="/filters",
    tags=["filters"],
    dependencies=[Depends(get_api_key)],
)


def validate_object_id(id: str) -> ObjectId:
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filter id",
        )
    return ObjectId(id)


@router.post("/", response_model=FilterModel, status_code=status.HTTP_201_CREATED)
async def create_filter(filter_data: FilterCreate):
    doc = filter_data.model_dump(mode="json")
    result = await filter_collection.insert_one(doc)
    created_filter = await filter_collection.find_one({
        "_id": result.inserted_id
    })
    return created_filter


@router.get("/", response_model=list[FilterModel])
async def list_filters(skip: int = 0, limit: int = 50):
    cursor = (
        filter_collection
        .find()
        .skip(skip)
        .limit(limit)
    )
    filters = await cursor.to_list(length=limit)
    return filters


@router.get("/{filter_id}", response_model=FilterModel)
async def get_filter(filter_id: str):
    object_id = validate_object_id(filter_id)
    filter_doc = await filter_collection.find_one({
        "_id": object_id
    })
    if not filter_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found",
        )
    return filter_doc


@router.put("/{filter_id}", response_model=FilterModel)
async def update_filter(filter_id: str, filter_data: FilterUpdate):
    object_id = validate_object_id(filter_id)
    update_data = filter_data.model_dump(
        mode="json",
        exclude_unset=True,
    )
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    updated_filter = await filter_collection.find_one_and_update(
        {"_id": object_id},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found",
        )
    return updated_filter


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(filter_id: str):
    object_id = validate_object_id(filter_id)
    result = await filter_collection.delete_one({
        "_id": object_id
    })
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found",
        )
    return None