"""核心接口冒烟测试。

这些测试只验证最重要的用户链路：服务启动、登录、读行程、生成并保存手账。
"""

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app


def test_health_and_authenticated_flow(monkeypatch) -> None:
    """演示账号应当能登录，并访问受保护的旅行数据。"""

    # 自动化测试固定使用本地模板，避免消耗真实模型额度。
    monkeypatch.setattr(settings, "ai_api_key", "")
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["database"] == "sqlite"

        login = client.post("/api/v1/auth/login", json={"account": "demo", "password": "demo1234"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        trips = client.get("/api/v1/trips", headers=headers)
        assert trips.status_code == 200
        assert trips.json()[0]["city"] == "大理"

        generated = client.post(
            "/api/v1/ai/journal",
            headers=headers,
            json={"journal_id": 1, "prompt": "突出傍晚的风", "style": "散文随笔"},
        )
        assert generated.status_code == 200
        assert generated.json()["content"]


def test_protected_endpoint_rejects_anonymous_request() -> None:
    """没有登录令牌时，私人行程接口必须拒绝访问。"""

    with TestClient(app) as client:
        response = client.get("/api/v1/trips")
        assert response.status_code == 401
