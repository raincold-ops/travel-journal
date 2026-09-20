"""多媒体附件的数据结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    journal_id: int | None
    media_type: str
    url: str
    file_name: str
    mime_type: str
    size_bytes: int
    duration_seconds: float | None
    latitude: float | None
    longitude: float | None
    taken_at: datetime | None
    ai_description: str | None
    ai_tags: str | None
    ai_analyzed_at: datetime | None
    created_at: datetime


class ImageAnalysisRequest(BaseModel):
    """用户可补充本次图片分析最关心的内容。"""

    prompt: str = "重点识别旅行场景、自然景观、建筑、食物和可用于手账的细节"


class ImageAnalysisResponse(BaseModel):
    """华为云视觉模型返回并写入数据库的结构化结果。"""

    media_id: int
    description: str
    scene: str | None = None
    landmark: str | None = None
    mood: str | None = None
    suggested_caption: str | None = None
    tags: list[str] = Field(default_factory=list)
    provider: str
