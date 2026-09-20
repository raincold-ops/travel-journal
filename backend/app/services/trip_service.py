"""行程与路线点业务。"""

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import RoutePoint, Trip
from backend.app.schemas.trip import RoutePointCreate, TripCreate, TripUpdate


def get_owned_trip(db: Session, trip_id: int, user_id: int) -> Trip:
    """取得属于当前用户的行程，不存在时统一返回 404。"""

    trip = db.scalar(
        select(Trip)
        .options(selectinload(Trip.route_points))
        .where(Trip.id == trip_id, Trip.user_id == user_id)
    )
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    return trip


def list_trips(db: Session, user_id: int, status_filter: str | None = None) -> list[Trip]:
    """按创建时间倒序列出当前用户的行程，可按状态筛选。"""

    statement = (
        select(Trip)
        .options(selectinload(Trip.route_points))
        .where(Trip.user_id == user_id)
        .order_by(Trip.start_date.desc())
    )
    if status_filter:
        statement = statement.where(Trip.status == status_filter)
    return list(db.scalars(statement).unique().all())


def create_trip(db: Session, user_id: int, payload: TripCreate) -> Trip:
    """创建行程，并一次性保存用户传入的路线点。"""

    trip_data = payload.model_dump(exclude={"route_points"})
    trip = Trip(user_id=user_id, **trip_data)
    trip.route_points = [
        RoutePoint(sequence=index, **point.model_dump())
        for index, point in enumerate(payload.route_points)
    ]
    db.add(trip)
    db.commit()
    return get_owned_trip(db, trip.id, user_id)


def update_trip(db: Session, trip: Trip, payload: TripUpdate) -> Trip:
    """只更新请求中出现的行程字段，并再次检查日期顺序。"""

    changes = payload.model_dump(exclude_unset=True)
    start_date = changes.get("start_date", trip.start_date)
    end_date = changes.get("end_date", trip.end_date)
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="结束日期不能早于开始日期")
    for field, value in changes.items():
        setattr(trip, field, value)
    db.commit()
    db.refresh(trip)
    return trip


def replace_route(db: Session, trip: Trip, points: list[RoutePointCreate]) -> Trip:
    """整体替换一条行程的路线，前端拖拽排序后可直接调用。"""

    db.execute(delete(RoutePoint).where(RoutePoint.trip_id == trip.id))
    db.add_all(
        [RoutePoint(trip_id=trip.id, sequence=index, **point.model_dump()) for index, point in enumerate(points)]
    )
    db.commit()
    return get_owned_trip(db, trip.id, trip.user_id)


def delete_trip(db: Session, trip: Trip) -> None:
    """删除行程；关联路线、手账和回忆会按模型关系一并删除。"""

    db.delete(trip)
    db.commit()

