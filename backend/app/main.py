"""FastAPI 应用入口。

运行命令：uvicorn backend.app.main:app --reload --port 8001
接口文档：http://localhost:8001/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.database import create_database_tables, engine
from backend.app.db.seed import seed_demo_data
from backend.app.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用启动时建表和填充演示数据，关闭时释放数据库连接池。"""

    create_database_tables()
    seed_demo_data()
    yield
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="旅行时光手账后端：账号、行程、手账、多媒体、地图、AI 与回忆精选。",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)
settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/health", response_model=HealthResponse, tags=["系统"])
def health_check() -> HealthResponse:
    """供前端或部署平台检查服务是否正常。"""

    return HealthResponse(
        status="ok",
        app=settings.app_name,
        database="sqlite",
        map_mode="browser-js-api",
        map_server_configured=bool(settings.baidu_map_ak),
        ai_mode=settings.ai_model if settings.ai_api_key else "local-template",
        vision_mode=settings.vision_model if settings.vision_api_key else "disabled",
    )
