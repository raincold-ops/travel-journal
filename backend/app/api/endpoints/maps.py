"""百度地图能力接口。"""

from typing import Annotated

from fastapi import APIRouter, Query

from backend.app.api.deps import CurrentUser
from backend.app.schemas.map import GeocodeResponse, ReverseGeocodeResponse, RouteRequest, RouteResponse
from backend.app.services import map_service


router = APIRouter(prefix="/map", tags=["05 · 地图"])


@router.get("/geocode", response_model=GeocodeResponse)
async def address_to_coordinate(
    current_user: CurrentUser,
    address: Annotated[str, Query(min_length=2, max_length=128)],
    city: Annotated[str | None, Query(max_length=40)] = None,
) -> GeocodeResponse:
    """将地址文字解析为百度坐标。"""

    return await map_service.geocode(address, city)


@router.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
async def coordinate_to_address(
    current_user: CurrentUser,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
) -> ReverseGeocodeResponse:
    """将百度坐标解析为省、市、区和街道。"""

    return await map_service.reverse_geocode(latitude, longitude)


@router.post("/driving-route", response_model=RouteResponse)
async def plan_driving_route(payload: RouteRequest, current_user: CurrentUser) -> RouteResponse:
    """规划两个坐标之间的驾车路线。"""

    return await map_service.driving_route(payload.origin, payload.destination)

