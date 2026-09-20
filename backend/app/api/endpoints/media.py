"""照片与语音上传接口。"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, Form, Response, UploadFile, status

from backend.app.api.deps import CurrentUser, Database
from backend.app.schemas.media import ImageAnalysisRequest, ImageAnalysisResponse, MediaResponse
from backend.app.services import media_service, vision_service


router = APIRouter(prefix="/media", tags=["04 · 多媒体"])


@router.post("/upload", response_model=MediaResponse, status_code=201)
async def upload_media(
    db: Database,
    current_user: CurrentUser,
    file: Annotated[UploadFile, File(description="照片或语音文件")],
    journal_id: Annotated[int | None, Form()] = None,
    duration_seconds: Annotated[float | None, Form()] = None,
    latitude: Annotated[float | None, Form()] = None,
    longitude: Annotated[float | None, Form()] = None,
    taken_at: Annotated[datetime | None, Form()] = None,
) -> MediaResponse:
    """上传照片或语音，并可关联到某篇手账。"""

    return await media_service.save_upload(
        db, current_user.id, file, journal_id, duration_seconds, latitude, longitude, taken_at
    )


@router.get("", response_model=list[MediaResponse])
def get_media(db: Database, current_user: CurrentUser, journal_id: int | None = None) -> list[MediaResponse]:
    """获取我的媒体文件，可按手账筛选。"""

    return media_service.list_media(db, current_user.id, journal_id)


@router.post("/{media_id}/analyze", response_model=ImageAnalysisResponse)
async def analyze_photo(
    media_id: int, payload: ImageAnalysisRequest, db: Database, current_user: CurrentUser
) -> ImageAnalysisResponse:
    """使用华为云 Qwen2.5-VL 分析一张已上传的旅行照片。"""

    return await vision_service.analyze_media(db, media_id, current_user.id, payload.prompt)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_media(media_id: int, db: Database, current_user: CurrentUser) -> Response:
    """删除媒体文件和元数据。"""

    media_service.delete_media(db, media_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
