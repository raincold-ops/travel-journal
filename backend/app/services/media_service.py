"""照片和语音上传、查询、删除业务。"""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models import Journal, Media


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/ogg", "audio/webm"}


def get_owned_media(db: Session, media_id: int, user_id: int) -> Media:
    """读取属于当前用户的媒体记录。"""

    media = db.scalar(select(Media).where(Media.id == media_id, Media.user_id == user_id))
    if not media:
        raise HTTPException(status_code=404, detail="媒体文件不存在")
    return media


async def save_upload(
    db: Session,
    user_id: int,
    file: UploadFile,
    journal_id: int | None,
    duration_seconds: float | None,
    latitude: float | None,
    longitude: float | None,
    taken_at: datetime | None,
) -> Media:
    """校验并落盘一个上传文件，然后在数据库保存元信息。"""

    if journal_id is not None:
        owned = db.scalar(select(Journal.id).where(Journal.id == journal_id, Journal.user_id == user_id))
        if not owned:
            raise HTTPException(status_code=404, detail="要绑定的手账不存在")

    mime_type = file.content_type or "application/octet-stream"
    base_mime_type = mime_type.split(";", 1)[0].strip().lower()
    if base_mime_type in ALLOWED_IMAGE_TYPES:
        media_type, folder = "photo", "photos"
    elif base_mime_type in ALLOWED_AUDIO_TYPES:
        media_type, folder = "audio", "audio"
    else:
        raise HTTPException(status_code=415, detail="仅支持 JPG/PNG/WebP/GIF 图片和常见音频格式")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"单个文件不能超过 {settings.max_upload_mb}MB")

    suffix = Path(file.filename or "file").suffix.lower()[:10]
    stored_name = f"{uuid4().hex}{suffix}"
    target_dir = settings.upload_dir / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / stored_name
    target_path.write_bytes(content)

    media = Media(
        user_id=user_id,
        journal_id=journal_id,
        media_type=media_type,
        url=f"/uploads/{folder}/{stored_name}",
        file_name=(file.filename or stored_name)[:255],
        mime_type=base_mime_type,
        size_bytes=len(content),
        duration_seconds=duration_seconds,
        latitude=latitude,
        longitude=longitude,
        taken_at=taken_at,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def list_media(db: Session, user_id: int, journal_id: int | None = None) -> list[Media]:
    """列出用户媒体，可按手账筛选。"""

    statement = select(Media).where(Media.user_id == user_id).order_by(Media.created_at.desc())
    if journal_id is not None:
        statement = statement.where(Media.journal_id == journal_id)
    return list(db.scalars(statement).all())


def delete_media(db: Session, media_id: int, user_id: int) -> None:
    """同时删除磁盘文件与数据库记录。"""

    media = get_owned_media(db, media_id, user_id)
    relative_path = media.url.removeprefix("/uploads/")
    file_path = (settings.upload_dir / relative_path).resolve()
    upload_root = settings.upload_dir.resolve()
    if file_path.is_relative_to(upload_root) and file_path.exists():
        file_path.unlink()
    db.delete(media)
    db.commit()
