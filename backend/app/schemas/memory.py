"""回忆精选的数据结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MemoryGenerateRequest(BaseModel):
    trip_id: int
    period: str | None = Field(default=None, max_length=50, examples=["2026年8月"])
    style: str = Field(default="温柔电影感", max_length=30)


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    title: str
    description: str
    generated_content: str
    cover_url: str | None
    period: str | None
    created_at: datetime

