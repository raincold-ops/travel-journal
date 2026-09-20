"""百度地图 Web API 的服务端代理。

AK 只保存在服务端；前端调用本项目接口，不会看到或泄露地图密钥。
"""

import re

import httpx
from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.schemas.map import Coordinate, RouteResponse


BAIDU_API = "https://api.map.baidu.com"


def _require_map_key() -> str:
    """在调用百度接口前检查 AK 是否已配置。"""

    if not settings.baidu_map_ak:
        raise HTTPException(status_code=503, detail="尚未配置百度地图服务端 AK")
    return settings.baidu_map_ak


async def _baidu_get(path: str, params: dict) -> dict:
    """发送百度地图请求，并将第三方错误转换成清晰的业务错误。"""

    safe_params = {**params, "ak": _require_map_key(), "output": "json"}
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(f"{BAIDU_API}{path}", params=safe_params)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="百度地图服务暂时不可用") from exc

    if data.get("status") != 0:
        message = data.get("message") or data.get("msg") or "请求失败"
        raise HTTPException(status_code=502, detail=f"百度地图返回错误：{message}")
    return data


async def geocode(address: str, city: str | None) -> dict:
    """把文字地址转换成百度经纬度。"""

    data = await _baidu_get("/geocoding/v3/", {"address": address, "city": city or ""})
    result = data["result"]
    return {
        "address": address,
        "latitude": result["location"]["lat"],
        "longitude": result["location"]["lng"],
        "precise": result.get("precise"),
        "confidence": result.get("confidence"),
    }


async def reverse_geocode(latitude: float, longitude: float) -> dict:
    """把百度经纬度转换成结构化地址。"""

    data = await _baidu_get(
        "/reverse_geocoding/v3/",
        {"location": f"{latitude},{longitude}", "coordtype": "bd09ll", "extensions_poi": 0},
    )
    result = data["result"]
    component = result.get("addressComponent", {})
    return {
        "formatted_address": result.get("formatted_address", ""),
        "province": component.get("province"),
        "city": component.get("city"),
        "district": component.get("district"),
        "street": component.get("street"),
        "business": result.get("business"),
    }


async def driving_route(origin: Coordinate, destination: Coordinate) -> RouteResponse:
    """规划两点之间的驾车路线，并整理出前端可直接绘制的坐标序列。"""

    data = await _baidu_get(
        "/directionlite/v1/driving",
        {
            "origin": f"{origin.latitude},{origin.longitude}",
            "destination": f"{destination.latitude},{destination.longitude}",
            "coord_type": "bd09ll",
            "steps_info": 1,
        },
    )
    routes = data.get("result", {}).get("routes", [])
    if not routes:
        raise HTTPException(status_code=404, detail="没有找到合适的驾车路线")

    route = routes[0]
    steps: list[dict] = []
    path: list[list[float]] = []
    for step in route.get("steps", []):
        instructions = re.sub(r"<[^>]+>", "", step.get("instructions", ""))
        steps.append(
            {
                "instruction": instructions,
                "distance_meters": step.get("distance", 0),
                "duration_seconds": step.get("duration", 0),
            }
        )
        for point in step.get("path", "").split(";"):
            if "," in point:
                longitude, latitude = point.split(",", 1)
                path.append([float(longitude), float(latitude)])

    return RouteResponse(
        distance_meters=route.get("distance", 0),
        duration_seconds=route.get("duration", 0),
        toll_yuan=route.get("toll"),
        steps=steps,
        raw_path=path,
    )
