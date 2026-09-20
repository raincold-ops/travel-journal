"""回忆精选接口。"""

from fastapi import APIRouter, Response, status

from backend.app.api.deps import CurrentUser, Database
from backend.app.schemas.memory import MemoryGenerateRequest, MemoryResponse
from backend.app.services import memory_service


router = APIRouter(prefix="/memories", tags=["07 · 回忆精选"])


@router.get("", response_model=list[MemoryResponse])
def get_memories(db: Database, current_user: CurrentUser) -> list[MemoryResponse]:
    """获取我的全部回忆精选。"""

    return memory_service.list_memories(db, current_user.id)


@router.post("/generate", response_model=MemoryResponse, status_code=201)
def create_memory(
    payload: MemoryGenerateRequest, db: Database, current_user: CurrentUser
) -> MemoryResponse:
    """根据一个已有手账的行程生成回忆精选。"""

    return memory_service.generate_memory(db, current_user.id, payload)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_memory(memory_id: int, db: Database, current_user: CurrentUser) -> Response:
    """删除一条回忆精选。"""

    memory_service.delete_memory(db, memory_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

