"""多个接口都会使用的通用响应结构。"""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """只需要返回处理结果消息时使用。"""

    message: str


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str
    app: str
    database: str
    map_mode: str
    map_server_configured: bool
    ai_mode: str
    vision_mode: str
