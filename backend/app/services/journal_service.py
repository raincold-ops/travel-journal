"""图文手账的增删改查业务。"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import Journal, Trip
from backend.app.schemas.journal import JournalCreate, JournalUpdate


def get_owned_journal(db: Session, journal_id: int, user_id: int) -> Journal:
    """获取当前用户的一篇手账，并同时读取媒体列表。"""

    journal = db.scalar(
        select(Journal)
        .options(selectinload(Journal.media))
        .where(Journal.id == journal_id, Journal.user_id == user_id)
    )
    if not journal:
        raise HTTPException(status_code=404, detail="手账不存在")
    return journal


def list_journals(db: Session, user_id: int, trip_id: int | None = None) -> list[Journal]:
    """列出用户手账；提供 trip_id 时只返回指定行程的内容。"""

    statement = (
        select(Journal)
        .options(selectinload(Journal.media))
        .where(Journal.user_id == user_id)
        .order_by(Journal.created_at.desc())
    )
    if trip_id is not None:
        statement = statement.where(Journal.trip_id == trip_id)
    return list(db.scalars(statement).unique().all())


def _ensure_trip_owned(db: Session, trip_id: int | None, user_id: int) -> None:
    """防止用户把手账关联到其他人的行程。"""

    if trip_id is not None and not db.scalar(select(Trip.id).where(Trip.id == trip_id, Trip.user_id == user_id)):
        raise HTTPException(status_code=404, detail="关联行程不存在")


def create_journal(db: Session, user_id: int, payload: JournalCreate) -> Journal:
    """创建一篇新手账。"""

    _ensure_trip_owned(db, payload.trip_id, user_id)
    journal = Journal(user_id=user_id, **payload.model_dump())
    db.add(journal)
    db.commit()
    return get_owned_journal(db, journal.id, user_id)


def update_journal(db: Session, journal: Journal, payload: JournalUpdate) -> Journal:
    """保存手账编辑器提交的局部修改。"""

    changes = payload.model_dump(exclude_unset=True)
    if "trip_id" in changes:
        _ensure_trip_owned(db, changes["trip_id"], journal.user_id)
    for field, value in changes.items():
        setattr(journal, field, value)
    db.commit()
    return get_owned_journal(db, journal.id, journal.user_id)


def delete_journal(db: Session, journal: Journal) -> None:
    """删除手账，数据库会同时删除其媒体记录。"""

    db.delete(journal)
    db.commit()

