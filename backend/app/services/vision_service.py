"""华为云 MaaS 图片理解服务。

本模块只负责“读取一张已上传图片 → 调用 Qwen2.5-VL → 保存结构化描述”。
日志生成服务只消费这里保存的文字结果，因此视觉模型和文本模型可以独立替换。
"""

import base64
import json
import re
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models import Media
from backend.app.schemas.media import ImageAnalysisResponse
from backend.app.services.media_service import get_owned_media


def _resolve_media_path(media: Media) -> Path:
    """将数据库 URL 安全转换为 uploads 目录内的真实文件路径。"""

    relative_path = media.url.removeprefix("/uploads/")
    file_path = (settings.upload_dir / relative_path).resolve()
    if not file_path.is_relative_to(settings.upload_dir.resolve()) or not file_path.is_file():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    return file_path


def _extract_json(content: str) -> dict:
    """兼容模型直接返回 JSON 或使用 Markdown 代码块包裹 JSON 的情况。"""

    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return {"description": cleaned}
        try:
            result = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {"description": cleaned}
    return result if isinstance(result, dict) else {"description": str(result)}


async def _call_huawei_vision(image_data_url: str, user_prompt: str) -> dict:
    """按华为云 OpenAI 兼容协议请求 Qwen2.5-VL。"""

    if not settings.vision_api_key:
        raise HTTPException(status_code=503, detail="尚未配置华为云 MaaS 图像理解 API Key")

    system_prompt = """你是旅行照片整理助手。分析图片中真实可见的内容，不确定时明确说不确定。
返回纯 JSON：description 为100字内客观描述，scene 为场景类型，landmark 为可识别地标或null，
mood 为氛围，suggested_caption 为一句文艺但不夸张的手账配文，tags 为最多8个短标签。"""
    body = {
        "model": settings.vision_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            },
        ],
        "temperature": 0.2,
        "max_tokens": 700,
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.vision_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.vision_api_key}"},
                json=body,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return _extract_json(content)
    except httpx.HTTPStatusError as exc:
        detail = "华为云视觉模型调用失败，请检查 Key、区域和模型权限"
        if exc.response.status_code == 401:
            detail = "华为云 MaaS API Key 无效或不属于当前服务区域"
        elif exc.response.status_code == 429:
            detail = "华为云视觉模型请求过多或额度不足"
        raise HTTPException(status_code=502, detail=detail) from exc
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="华为云视觉模型暂时不可用") from exc


async def analyze_media(
    db: Session, media_id: int, user_id: int, user_prompt: str
) -> ImageAnalysisResponse:
    """分析用户的一张照片，将结果写入媒体记录并返回给前端。"""

    media = get_owned_media(db, media_id, user_id)
    if media.media_type != "photo":
        raise HTTPException(status_code=422, detail="只有照片可以使用图像理解")

    file_path = _resolve_media_path(media)
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    image_data_url = f"data:{media.mime_type};base64,{encoded}"
    result = await _call_huawei_vision(image_data_url, user_prompt)

    tags = result.get("tags") or []
    if not isinstance(tags, list):
        tags = [str(tags)]
    description = str(result.get("description") or "图片分析完成")
    media.ai_description = description
    media.ai_tags = json.dumps(tags[:8], ensure_ascii=False)
    media.ai_analyzed_at = datetime.now()
    db.commit()
    db.refresh(media)

    return ImageAnalysisResponse(
        media_id=media.id,
        description=description,
        scene=result.get("scene"),
        landmark=result.get("landmark"),
        mood=result.get("mood"),
        suggested_caption=result.get("suggested_caption"),
        tags=[str(tag) for tag in tags[:8]],
        provider=settings.vision_model,
    )
