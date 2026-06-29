from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Any
from bson import ObjectId
from pydantic_core import core_schema
from datetime import datetime
from pydantic import ConfigDict


class PydanticObjectId(ObjectId):
    """
    MongoDB ObjectId wrapped for Pydantic v2 JSON schema support.
    Serializes to string, validates both ObjectId and string inputs.
    """
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        """Generate Pydantic core schema for ObjectId validation and serialization"""
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v) if isinstance(v, ObjectId) else v,
                return_schema=core_schema.str_schema(),
                when_used='json'
            )
        )
    
    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        """Validate and convert input to ObjectId"""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if not ObjectId.is_valid(v):
                raise ValueError(f'Invalid ObjectId format: {v}')
            return cls(v)
        raise TypeError(f'ObjectId or string required, got {type(v).__name__}')


class JobCreate(BaseModel):
    title: str
    company: str
    level: str
    link: HttpUrl
    source: str
    posted_at: datetime | str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class JobModel(BaseModel):
    """Response model for Job with optional fields for backward compatibility"""
    id: Optional[PydanticObjectId] = Field(alias="_id", default=None)
    title: str
    company: str | None = None
    level: str | None = None
    link: HttpUrl | None = None
    source: str | None = None
    posted_at: datetime | None = None
    dedup_key: str | None = None
    scraped_at: datetime | None = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    level: str | None = None
    link: HttpUrl | None = None
    source: str | None = None
    posted_at: datetime | str | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

class JobCollection(BaseModel):
    jobs: List[JobModel]
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

class ScraperConfigCreate(BaseModel):
    name: str = Field(min_length=1)
    source: str = Field(min_length=1)
    url: HttpUrl
    active: bool = True
    schedule_hours: int = Field(default=2, gt=0)