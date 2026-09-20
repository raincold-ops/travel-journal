"""AI 日志生成的数据结构。"""

from pydantic import BaseModel, Field


class JournalGenerateRequest(BaseModel):
    trip_id: int | None = None
    journal_id: int | None = None
    prompt: str = Field(default="", max_length=1000)
    style: str = Field(default="散文随笔", max_length=30)
    save_as_draft: bool = True


class JournalGenerateResponse(BaseModel):
    title: str
    content: str
    provider: str
    journal_id: int | None = None

