"""行程与路线点接口。"""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from backend.app.api.deps import CurrentUser, Database
from backend.app.schemas.trip import RouteReplaceRequest, TripCreate, TripResponse, TripUpdate
from backend.app.services import trip_service


router = APIRouter(prefix="/trips", tags=["02 · 行程"])


@router.get("", response_model=list[TripResponse])
def get_trips(
    db: Database,
    current_user: CurrentUser,
    trip_status: Annotated[str | None, Query(alias="status")] = None,
) -> list[TripResponse]:
    """获取我的全部行程，可用 status 筛选。"""

    return trip_service.list_trips(db, current_user.id, trip_status)


@router.post("", response_model=TripResponse, status_code=201)
def add_trip(payload: TripCreate, db: Database, current_user: CurrentUser) -> TripResponse:
    """新建行程，可在同一请求中提交路线点。"""

    return trip_service.create_trip(db, current_user.id, payload)


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: int, db: Database, current_user: CurrentUser) -> TripResponse:
    """读取一个行程详情。"""

    return trip_service.get_owned_trip(db, trip_id, current_user.id)


@router.patch("/{trip_id}", response_model=TripResponse)
def edit_trip(trip_id: int, payload: TripUpdate, db: Database, current_user: CurrentUser) -> TripResponse:
    """局部更新一个行程。"""

    trip = trip_service.get_owned_trip(db, trip_id, current_user.id)
    return trip_service.update_trip(db, trip, payload)


@router.put("/{trip_id}/route", response_model=TripResponse)
def set_route(
    trip_id: int, payload: RouteReplaceRequest, db: Database, current_user: CurrentUser
) -> TripResponse:
    """保存地图中排好顺序的全部路线点。"""

    trip = trip_service.get_owned_trip(db, trip_id, current_user.id)
    return trip_service.replace_route(db, trip, payload.points)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_trip(trip_id: int, db: Database, current_user: CurrentUser) -> Response:
    """删除行程及其关联数据。"""

    trip = trip_service.get_owned_trip(db, trip_id, current_user.id)
    trip_service.delete_trip(db, trip)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

