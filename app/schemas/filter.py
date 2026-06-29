from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, HttpUrl, BeforeValidator, field_validator, ConfigDict
from typing_extensions import Annotated


PyObjectId = Annotated[str, BeforeValidator(str)]


class FilterCreate(BaseModel):
    level: Optional[str] = None
    stack: list[str] = Field(default_factory=list)
    source: Optional[str] = None
    discord_webhook: HttpUrl
    active: bool = True

    @field_validator("level", "source")
    @classmethod
    def normalize_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()
        return value or None

    @field_validator("stack")
    @classmethod
    def normalize_stack(cls, value: list[str]) -> list[str]:
        return sorted({
            item.strip().lower()
            for item in value
            if item.strip()
        })


class FilterUpdate(BaseModel):
    level: Optional[str] = None
    stack: Optional[list[str]] = None
    source: Optional[str] = None
    discord_webhook: Optional[HttpUrl] = None
    active: Optional[bool] = None

    @field_validator("level", "source")
    @classmethod
    def normalize_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()
        return value or None

    @field_validator("stack")
    @classmethod
    def normalize_stack(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None

        return sorted({
            item.strip().lower()
            for item in value
            if item.strip()
        })


class FilterModel(FilterCreate):
    id: PyObjectId = Field(alias="_id")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )