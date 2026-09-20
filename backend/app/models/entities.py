"""数据库表定义。

每个类对应 SQLite 中的一张表；relationship 用来描述表之间的关系。
"""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


def now_local() -> datetime:
    """返回不带时区的当前时间，适合 SQLite 存储。"""

    return datetime.now()


class User(Base):
    """用户账号与个人资料。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str] = mapped_column(String(200), default="在地图上写诗，在风景里生活。")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    trips: Mapped[list["Trip"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    journals: Mapped[list["Journal"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Trip(Base):
    """一次完整旅行，例如“大理慢游”。"""

    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(80))
    province: Mapped[str | None] = mapped_column(String(80), nullable=True)
    country: Mapped[str] = mapped_column(String(80), default="中国")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planning")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    user: Mapped[User] = relationship(back_populates="trips")
    route_points: Mapped[list["RoutePoint"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", order_by="RoutePoint.sequence"
    )
    journals: Mapped[list["Journal"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    memories: Mapped[list["Memory"]] = relationship(back_populates="trip", cascade="all, delete-orphan")


class RoutePoint(Base):
    """行程路线中的一个地点。"""

    __tablename__ = "route_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    visited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    trip: Mapped[Trip] = relationship(back_populates="route_points")


class Journal(Base):
    """用户编写或 AI 生成的一篇旅行手账。"""

    __tablename__ = "journals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(150))
    content: Mapped[str] = mapped_column(Text, default="")
    mood: Mapped[str | None] = mapped_column(String(30), nullable=True)
    weather: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)

    user: Mapped[User] = relationship(back_populates="journals")
    trip: Mapped[Trip | None] = relationship(back_populates="journals")
    media: Mapped[list["Media"]] = relationship(back_populates="journal", cascade="all, delete-orphan")


class Media(Base):
    """手账中的照片或语音文件及其元数据。"""

    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    journal_id: Mapped[int | None] = mapped_column(ForeignKey("journals.id"), nullable=True, index=True)
    media_type: Mapped[str] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(500))
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ai_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    journal: Mapped[Journal | None] = relationship(back_populates="media")


class Memory(Base):
    """从行程、手账和照片中整理出的回忆精选。"""

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    generated_content: Mapped[str] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    period: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    trip: Mapped[Trip] = relationship(back_populates="memories")
