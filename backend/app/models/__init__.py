"""导出数据库实体，确保建表时 SQLAlchemy 能发现全部模型。"""

from backend.app.models.entities import Journal, Media, Memory, RoutePoint, Trip, User

__all__ = ["User", "Trip", "RoutePoint", "Journal", "Media", "Memory"]

