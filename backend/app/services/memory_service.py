"""回忆精选生成与查询业务。"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import Journal, Memory, Trip
from backend.app.schemas.memory import MemoryGenerateRequest
from backend.app.services.trip_service import get_owned_trip


def list_memories(db: Session, user_id: int) -> list[Memory]:
    """按生成时间倒序列出当前用户的回忆精选。"""

    return list(
        db.scalars(select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.desc())).all()
    )


def generate_memory(db: Session, user_id: int, payload: MemoryGenerateRequest) -> Memory:
    """从指定行程的日志中整理一篇回忆精选并保存。"""

    trip = get_owned_trip(db, payload.trip_id, user_id)
    journals = list(
        db.scalars(
            select(Journal)
            .options(selectinload(Journal.media))
            .where(Journal.trip_id == trip.id, Journal.user_id == user_id)
            .order_by(Journal.created_at)
        ).unique().all()
    )
    if not journals:
        raise HTTPException(status_code=422, detail="这个行程还没有手账，暂时无法生成回忆")

    selected_lines = [journal.content.strip().split("\n", 1)[0][:180] for journal in journals if journal.content.strip()]
    highlight = "\n\n".join(selected_lines[:5]) or "这段旅程还留有很多等待书写的空白。"
    media_count = sum(len(journal.media) for journal in journals)
    title = f"{trip.city}，一场缓慢的相遇"
    description = f"{len(journals)} 篇手账 · {media_count} 个多媒体片段 · {payload.style}"
    generated_content = (
        f"从 {trip.start_date} 到 {trip.end_date}，我们在{trip.city}收藏了一段属于自己的时间。\n\n"
        f"{highlight}\n\n回头看，旅行留下的不只是目的地，还有当时的天气、声音和心情。"
    )
    cover_url = trip.cover_url
    if not cover_url:
        for journal in journals:
            photo = next((item for item in journal.media if item.media_type == "photo"), None)
            if photo:
                cover_url = photo.url
                break

    memory = Memory(
        user_id=user_id,
        trip_id=trip.id,
        title=title,
        description=description,
        generated_content=generated_content,
        cover_url=cover_url,
        period=payload.period or trip.start_date.strftime("%Y年%m月"),
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def delete_memory(db: Session, memory_id: int, user_id: int) -> None:
    """删除一条属于当前用户的回忆精选。"""

    memory = db.scalar(select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id))
    if not memory:
        raise HTTPException(status_code=404, detail="回忆精选不存在")
    db.delete(memory)
    db.commit()

