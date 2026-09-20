"""旅行手账接口。"""

from fastapi import APIRouter, Response, status

from backend.app.api.deps import CurrentUser, Database
from backend.app.schemas.journal import JournalCreate, JournalResponse, JournalUpdate
from backend.app.services import journal_service


router = APIRouter(prefix="/journals", tags=["03 · 手账"])


@router.get("", response_model=list[JournalResponse])
def get_journals(db: Database, current_user: CurrentUser, trip_id: int | None = None) -> list[JournalResponse]:
    """获取我的手账，可用 trip_id 按行程筛选。"""

    return journal_service.list_journals(db, current_user.id, trip_id)


@router.post("", response_model=JournalResponse, status_code=201)
def add_journal(payload: JournalCreate, db: Database, current_user: CurrentUser) -> JournalResponse:
    """新建一篇手账或草稿。"""

    return journal_service.create_journal(db, current_user.id, payload)


@router.get("/{journal_id}", response_model=JournalResponse)
def get_journal(journal_id: int, db: Database, current_user: CurrentUser) -> JournalResponse:
    """读取一篇手账及它的媒体附件。"""

    return journal_service.get_owned_journal(db, journal_id, current_user.id)


@router.patch("/{journal_id}", response_model=JournalResponse)
def edit_journal(
    journal_id: int, payload: JournalUpdate, db: Database, current_user: CurrentUser
) -> JournalResponse:
    """自动保存或发布手账时调用。"""

    journal = journal_service.get_owned_journal(db, journal_id, current_user.id)
    return journal_service.update_journal(db, journal, payload)


@router.delete("/{journal_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_journal(journal_id: int, db: Database, current_user: CurrentUser) -> Response:
    """删除一篇手账。"""

    journal = journal_service.get_owned_journal(db, journal_id, current_user.id)
    journal_service.delete_journal(db, journal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

