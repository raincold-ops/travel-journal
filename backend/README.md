# travel01 后端说明

这是一个面向初学者组织的 FastAPI + SQLite 后端。开发时从项目根目录运行 `npm run dev`，会同时启动：

- 前端：<http://localhost:5174>
- 后端接口：<http://localhost:8001>
- Swagger 接口文档：<http://localhost:8001/docs>
- 健康检查：<http://localhost:8001/health>

演示账号为 `demo`，密码为 `demo1234`。

## 目录怎么读

```text
backend/
├─ app/
│  ├─ main.py              # 应用入口：组装路由、中间件、静态文件
│  ├─ core/                # 基础设施：配置、数据库、密码与令牌
│  ├─ models/entities.py   # SQLite 数据表定义
│  ├─ schemas/             # 接口输入和输出的数据格式
│  ├─ api/endpoints/       # URL 路由：只负责收参和返回结果
│  ├─ services/            # 业务逻辑：每个功能真正做事的地方
│  └─ db/seed.py           # 第一次启动时创建演示数据
├─ tests/                  # 自动化测试
├─ uploads/                # 用户上传内容，运行后自动创建
├─ data/                   # SQLite 文件，运行后自动创建
├─ .env                    # 本机密钥，不会提交到 Git
└─ requirements.txt        # Python 依赖
```

请求经过的路径很固定：

```text
浏览器 → api/endpoints → services → models → SQLite
   ├─ 百度地图 WebGL JS API（浏览器端 AK）
   └─ 后端 → DeepSeek / 华为云 MaaS
```

例如保存手账时：`journals.py` 接收请求，`journal_service.py` 检查行程归属并保存，`entities.py` 中的 `Journal` 决定表字段。

## 已实现接口

- `auth`：注册、登录、当前用户、修改资料
- `trips`：行程增删改查、整条路线保存
- `journals`：手账增删改查、草稿和发布状态
- `media`：图片/语音上传、列表、删除、位置元数据、华为云图片理解
- `map`：可选的服务端地址解析接口（只有另行申请服务端 AK 时使用）
- `ai`：根据行程/路线/手账/媒体摘要生成日志
- `memories`：从一次行程的多篇手账生成回忆精选

除注册和登录外，业务接口都要带：

```text
Authorization: Bearer 登录接口返回的令牌
```

## AI 模型配置

文本生成使用 DeepSeek，图像理解使用华为云 MaaS。两者的结果会串联：先分析照片，生成手账时会自动读取照片描述。

```env
AI_API_KEY=你的模型Key
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

VISION_API_KEY=你的华为云MaaS Key
VISION_BASE_URL=https://api.modelarts-maas.com/v1
VISION_MODEL=qwen2.5-vl-72b
```

图片工作流：先调用 `POST /media/upload` 上传，再调用 `POST /media/{media_id}/analyze` 分析。分析结果会写回媒体表。

## 百度地图配置

当前 AK 是“浏览器端”应用，因此应配置在项目根目录的 `.env.local`，由 Vue 直接加载百度 WebGL JS API：

```env
VITE_BAIDU_MAP_AK=你的浏览器端AK
```

足迹页已使用浏览器端能力完成底图、地点检索、定位、逆地理编码，以及驾车/步行/骑行路线规划。`backend/.env` 中的 `BAIDU_MAP_AK` 特意留空，避免把浏览器端 AK 错用于服务端 REST 接口。正式上线时请在百度控制台把 Referer 白名单从 `*` 改成实际域名；本地开发可加入 `localhost:*` 与 `127.0.0.1:*`。

## 单独运行和测试

```bash
conda activate trip
uvicorn backend.app.main:app --reload --port 8001
pytest backend/tests -q
```

生产环境部署前，请务必将 `.env` 中的 `SECRET_KEY` 更换为随机长字符串。
