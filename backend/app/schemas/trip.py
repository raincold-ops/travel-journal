"""行程和路线点的数据结构。"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RoutePointCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=300)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    visited_at: datetime | None = None


class RoutePointResponse(RoutePointCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sequence: int


class TripBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=80)
    province: str | None = Field(default=None, max_length=80)
    country: str = Field(default="中国", max_length=80)
    start_date: date
    end_date: date
    description: str | None = None
    cover_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="planning", pattern="^(planning|traveling|completed)$")

    @model_validator(mode="after")
    def validate_dates(self) -> "TripBase":
        """结束日期不能早于开始日期。"""

        if self.end_date < self.start_date:
            raise ValueError("结束日期不能早于开始日期")
        return self


class TripCreate(TripBase):
    route_points: list[RoutePointCreate] = Field(default_factory=list)


class TripUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=80)
    province: str | None = None
    country: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    cover_url: str | None = None
    status: str | None = Field(default=None, pattern="^(planning|traveling|completed)$")


class TripResponse(TripBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    route_points: list[RoutePointResponse] = Field(default_factory=list)


class RouteReplaceRequest(BaseModel):
    points: list[RoutePointCreate] = Field(min_length=1, max_length=100)
