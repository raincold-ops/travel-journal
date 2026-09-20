"""百度地图代理接口的数据结构。"""

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class GeocodeResponse(Coordinate):
    address: str
    precise: int | None = None
    confidence: int | None = None


class ReverseGeocodeResponse(BaseModel):
    formatted_address: str
    province: str | None = None
    city: str | None = None
    district: str | None = None
    street: str | None = None
    business: str | None = None


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate


class RouteResponse(BaseModel):
    distance_meters: int
    duration_seconds: int
    toll_yuan: float | None = None
    steps: list[dict]
    raw_path: list[list[float]]
