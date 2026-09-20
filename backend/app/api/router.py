"""统一组合全部 v1 接口。"""

from fastapi import APIRouter

from backend.app.api.endpoints import ai, auth, journals, maps, media, memories, trips


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(trips.router)
api_router.include_router(journals.router)
api_router.include_router(media.router)
api_router.include_router(maps.router)
api_router.include_router(ai.router)
api_router.include_router(memories.router)

