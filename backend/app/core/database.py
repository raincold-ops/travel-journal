"""数据库连接与会话管理。"""

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import BACKEND_DIR, settings


class Base(DeclarativeBase):
    """所有数据库模型的共同父类。"""


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """为一次 HTTP 请求提供数据库会话，请求结束后自动关闭。"""

    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


def create_database_tables() -> None:
    """首次启动时创建尚不存在的数据表。"""

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (BACKEND_DIR / "data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()


def _apply_lightweight_migrations() -> None:
    """为开发期旧数据库补充新增字段。

    正式生产项目建议换成 Alembic；这里保留一个很小的迁移器，让初学者拉取代码后
    不必删除已有 SQLite 数据也能继续运行。
    """

    existing = {column["name"] for column in inspect(engine).get_columns("media")}
    additions = {
        "ai_description": "TEXT",
        "ai_tags": "TEXT",
        "ai_analyzed_at": "DATETIME",
    }
    with engine.begin() as connection:
        for column, sql_type in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE media ADD COLUMN {column} {sql_type}"))
