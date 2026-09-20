"""创建首次启动即可体验的演示账号和旅行数据。"""

from datetime import date, datetime

from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.core.security import hash_password
from backend.app.models import Journal, RoutePoint, Trip, User


def seed_demo_data() -> None:
    """数据库为空时创建 demo/demo1234 账号及一组大理数据。"""

    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == "demo")):
            return

        user = User(
            username="demo",
            email="hello@lvye.cn",
            password_hash=hash_password("demo1234"),
            avatar_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=240",
        )
        trip = Trip(
            user=user,
            title="大理慢游",
            city="大理",
            province="云南",
            country="中国",
            start_date=date(2026, 8, 16),
            end_date=date(2026, 8, 21),
            status="completed",
            description="沿洱海慢慢走，把时间交给风。",
            cover_url="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1200",
        )
        trip.route_points = [
            RoutePoint(sequence=0, name="喜洲古镇", address="云南省大理市喜洲镇", latitude=25.851, longitude=100.123),
            RoutePoint(sequence=1, name="洱海生态廊道", address="云南省大理市环海西路", latitude=25.743, longitude=100.177),
            RoutePoint(sequence=2, name="龙龛码头", address="云南省大理市龙龛村", latitude=25.679, longitude=100.192),
        ]
        journal = Journal(
            user=user,
            trip=trip,
            title="在洱海边，等一场日落",
            content="风从苍山越过来，把湖面吹成一匹闪着银光的绸缎。我们沿着环海西路慢慢骑行，没有赶时间，也没有特意寻找风景。",
            mood="松弛",
            weather="23°C 晴",
            location_name="洱海生态廊道",
            latitude=25.743,
            longitude=100.177,
            is_draft=False,
            created_at=datetime(2026, 8, 18, 18, 20),
        )
        db.add_all([user, trip, journal])
        db.commit()

