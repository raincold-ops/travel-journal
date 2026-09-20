"""AI 旅行日志生成服务。

有模型 Key 时调用兼容 OpenAI 协议的模型；没有 Key 时使用本地模板生成，保证
开发和演示阶段功能不会中断。以后更换模型只需要修改 .env，无需改路由代码。
"""

import json

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.config import settings
from backend.app.models import Journal, Media, Trip
from backend.app.schemas.ai import JournalGenerateRequest, JournalGenerateResponse
from backend.app.services.journal_service import get_owned_journal
from backend.app.services.trip_service import get_owned_trip


def _collect_context(db: Session, user_id: int, payload: JournalGenerateRequest) -> dict:
    """从行程、已有手账和媒体中收集 AI 写作素材。"""

    trip = get_owned_trip(db, payload.trip_id, user_id) if payload.trip_id else None
    journal = get_owned_journal(db, payload.journal_id, user_id) if payload.journal_id else None
    if not trip and journal and journal.trip_id:
        trip = get_owned_trip(db, journal.trip_id, user_id)

    media_statement = select(Media).where(Media.user_id == user_id)
    if journal:
        media_statement = media_statement.where(Media.journal_id == journal.id)
    media = list(db.scalars(media_statement.limit(30)).all())

    return {
        "trip": trip,
        "journal": journal,
        "media_count": len(media),
        "photo_count": sum(item.media_type == "photo" for item in media),
        "audio_count": sum(item.media_type == "audio" for item in media),
        "photo_insights": [item.ai_description for item in media if item.ai_description][:12],
    }


def _build_prompt(context: dict, payload: JournalGenerateRequest) -> str:
    """把结构化旅行素材整理成稳定、容易调试的中文提示词。"""

    trip: Trip | None = context["trip"]
    journal: Journal | None = context["journal"]
    route_names = "、".join(point.name for point in trip.route_points) if trip else "未记录"
    return f"""你是一位克制、真诚的旅行手账作者。请根据素材写一篇中文旅行日志。
文字风格：{payload.style}
用户补充：{payload.prompt or '无'}
旅行：{trip.title if trip else '自由旅行'}
地点：{trip.city if trip else (journal.location_name if journal else '旅途中')}
日期：{f'{trip.start_date} 至 {trip.end_date}' if trip else '今天'}
路线地点：{route_names}
已有标题：{journal.title if journal else '无'}
已有文字：{journal.content[:1200] if journal else '无'}
照片数量：{context['photo_count']}，语音数量：{context['audio_count']}
视觉模型识别到的照片内容：{'；'.join(context['photo_insights']) or '尚未分析照片内容'}

只返回 JSON，格式为 {{"title":"20字以内标题","content":"2至4段正文"}}。
不要杜撰具体人物姓名、消费金额或没有出现在素材里的事实。"""


def _template_result(context: dict, payload: JournalGenerateRequest) -> tuple[str, str]:
    """模型未配置时，根据真实行程数据生成可编辑的本地示例。"""

    trip: Trip | None = context["trip"]
    journal: Journal | None = context["journal"]
    city = trip.city if trip else (journal.location_name if journal and journal.location_name else "远方")
    route_names = [point.name for point in trip.route_points] if trip else []
    place_line = "、".join(route_names[:3]) or city
    title = journal.title if journal and journal.title else f"在{city}，把时间慢下来"
    personal_note = f"我还记得：{payload.prompt.strip()}" if payload.prompt.strip() else "没有赶时间，也没有刻意寻找风景。"
    visual_note = context["photo_insights"][0] if context["photo_insights"] else "光落在远处的屋檐和树梢上"
    content = (
        f"今天的路从{place_line}慢慢展开。风掠过衣角，{visual_note}，"
        f"那些原本普通的片刻，因为身在{city}，忽然有了值得收藏的温度。\n\n"
        f"{personal_note} 旅行大概就是这样——不是急着抵达更多地方，而是在某个瞬间，"
        "真正看见眼前的生活。等以后再次翻开这一页，希望还能想起今天的风。"
    )
    return title[:150], content


async def _request_model(prompt: str) -> tuple[str, str]:
    """调用兼容 OpenAI Chat Completions 的模型并解析 JSON 返回值。"""

    endpoint = f"{settings.ai_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.ai_api_key}"}
    body = {
        "model": settings.ai_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "response_format": {"type": "json_object"},
    }
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(endpoint, headers=headers, json=body)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            result = json.loads(content)
            return str(result["title"])[:150], str(result["content"])
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI 模型暂时未能生成内容，请稍后重试") from exc


async def generate_journal(
    db: Session, user_id: int, payload: JournalGenerateRequest
) -> JournalGenerateResponse:
    """生成旅行日志；可选择把结果新建为草稿或更新到指定手账。"""

    context = _collect_context(db, user_id, payload)
    if settings.ai_api_key:
        title, content = await _request_model(_build_prompt(context, payload))
        provider = settings.ai_model
    else:
        title, content = _template_result(context, payload)
        provider = "local-template"

    journal: Journal | None = context["journal"]
    if journal:
        journal.title = title
        journal.content = content
        journal.ai_generated = True
        journal.is_draft = payload.save_as_draft
        db.commit()
        db.refresh(journal)
    elif payload.save_as_draft:
        trip: Trip | None = context["trip"]
        journal = Journal(
            user_id=user_id,
            trip_id=trip.id if trip else None,
            title=title,
            content=content,
            location_name=trip.city if trip else None,
            is_draft=True,
            ai_generated=True,
        )
        db.add(journal)
        db.commit()
        db.refresh(journal)

    return JournalGenerateResponse(
        title=title,
        content=content,
        provider=provider,
        journal_id=journal.id if journal else None,
    )
