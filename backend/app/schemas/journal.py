"""旅行手账的数据结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JournalCreate(BaseModel):
    trip_id: int | None = None
    title: str = Field(min_length=1, max_length=150)
    content: str = ""
    mood: str | None = Field(default=None, max_length=30)
    weather: str | None = Field(default=None, max_length=50)
    location_name: str | None = Field(default=None, max_length=200)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_draft: bool = True
    ai_generated: bool = False


class JournalUpdate(BaseModel):
    trip_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=150)
    content: str | None = None
    mood: str | None = None
    weather: str | None = None
    location_name: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_draft: bool | None = None


class MediaSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    media_type: str
    url: str
    file_name: str


class JournalResponse(JournalCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    media: list[MediaSummary] = Field(default_factory=list)
