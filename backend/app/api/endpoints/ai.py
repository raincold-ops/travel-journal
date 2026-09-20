"""AI 写作接口。"""

from fastapi import APIRouter

from backend.app.api.deps import CurrentUser, Database
from backend.app.schemas.ai import JournalGenerateRequest, JournalGenerateResponse
from backend.app.services import ai_service


router = APIRouter(prefix="/ai", tags=["06 · AI 辅助"])


@router.post("/journal", response_model=JournalGenerateResponse)
async def create_ai_journal(
    payload: JournalGenerateRequest, db: Database, current_user: CurrentUser
) -> JournalGenerateResponse:
    """根据行程、手账和多媒体摘要生成旅行日志。"""

    return await ai_service.generate_journal(db, current_user.id, payload)

