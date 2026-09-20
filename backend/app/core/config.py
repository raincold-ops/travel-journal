"""集中管理项目配置。

其他文件不要直接读取环境变量，统一从 ``settings`` 获取，方便开发者快速
知道项目有哪些可配置项，也方便以后部署到云服务器。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """应用运行所需的全部配置。"""

    app_name: str = "travel01 API"
    debug: bool = True
    api_prefix: str = "/api/v1"
    secret_key: str = "change-me"
    token_expire_minutes: int = 60 * 24 * 7

    database_url: str = f"sqlite:///{(BACKEND_DIR / 'data' / 'travel01.db').as_posix()}"
    upload_dir: Path = BACKEND_DIR / "uploads"
    max_upload_mb: int = 20

    baidu_map_ak: str = ""
    ai_api_key: str = ""
    ai_base_url: str = "https://api.deepseek.com/v1"
    ai_model: str = "deepseek-chat"
    vision_api_key: str = ""
    vision_base_url: str = "https://api.modelarts-maas.com/v1"
    vision_model: str = "qwen2.5-vl-72b"

    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """把逗号分隔的前端地址转换成 CORS 可用列表。"""

        return [item.strip() for item in self.frontend_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """只创建一次配置对象，避免每次请求重复读取 .env。"""

    return Settings()


settings = get_settings()
