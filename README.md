# AI Chat RAG

一个支持多用户、多会话、文件知识库、RAG 检索增强、多模型配置、图片识别和图片生成的 AI 聊天系统。项目包含前端聊天交互、后端会话管理、文件知识库索引、混合检索、动态 RAG Prompt、引用来源展示和 Docker 部署配置。

## 功能特性

- 用户注册、登录和 JWT 鉴权
- 多会话管理与历史消息展示
- MySQL 持久化保存用户、会话、消息、文件元数据和 RAG 监控记录
- Redis 缓存最近对话上下文
- 长对话 Summary Memory 压缩
- 用户自定义 OpenAI 兼容模型配置，支持多个模型配置切换
- 可选配置生图模型，由聊天模型自动判断是否需要生成图片
- 文件上传、删除、重新索引和知识库文件管理
- PDF 与常见文本类型解析
- 聊天图片附件独立上传，不进入知识库和 RAG
- 多模态识图：图片附件直接进入视觉模型分支
- 语义切片与多维 metadata 标注
- Chroma 向量知识库
- BM25 + 向量检索 Hybrid Search
- Query Rewrite 查询重写
- RAG Router 判断是否使用知识库
- 综合型问题多路查询扩展
- 回答引用来源展示
- RAG 监控记录与质量预判
- Docker Compose 一键部署

## 技术栈

### 前端

- React
- TypeScript
- Vite
- Ant Design
- CSS Modules

### 后端

- FastAPI
- SQLAlchemy
- Alembic
- MySQL
- Redis
- ChromaDB
- LangChain OpenAI
- sentence-transformers
- jieba
- rank-bm25
- OpenAI SDK

## 系统架构

```mermaid
flowchart TD
    A["React 前端"] --> B["FastAPI 后端"]
    B --> C["JWT 鉴权"]
    B --> D["MySQL"]
    B --> E["Redis"]
    B --> F["文件解析服务"]
    F --> G["语义切片"]
    G --> H["Embedding"]
    H --> I["Chroma 向量库"]
    B --> J["Query Rewrite"]
    B --> K["RAG Router"]
    K --> L["Hybrid Search"]
    L --> M["动态 RAG Prompt"]
    B --> O["聊天附件服务"]
    O --> P["多模态识图"]
    B --> S["Image Router"]
    S --> T["图片生成"]
    M --> N["OpenAI 兼容模型"]
    P --> N
    T --> N
    N --> A
```

## RAG 工作流

```mermaid
flowchart TD
    A["用户提问"] --> B["查询重写"]
    B --> C["判断是否需要知识库"]
    C -->|否| D["普通对话"]
    C -->|是| E["判断问题类型"]
    E -->|lookup| F["精确检索"]
    E -->|synthesis| G["多路查询扩展"]
    F --> H["BM25 + 向量检索"]
    G --> H
    H --> I["去重与排序"]
    I --> J["构造知识库上下文"]
    J --> K["大模型回答"]
    K --> L["返回答案和引用来源"]
```

## 上下文记忆设计

系统同时使用 MySQL 和 Redis 管理会话上下文：

- MySQL 保存全量消息历史，保证数据可靠持久化。
- Redis 保存最近上下文，减少每轮对话读取完整历史的成本。
- 当上下文过长时，后端会把旧消息与旧摘要合并生成新的 Summary Memory。
- 模型实际收到的是长期摘要加最近若干轮消息。

## 知识库入库流程

文件上传后，后端会执行：

```text
文件保存
 ↓
文档解析
 ↓
文本清洗
 ↓
语义切片
 ↓
metadata 标注
 ↓
Embedding
 ↓
写入 Chroma
```

当前 chunk metadata 包括：

```json
{
  "user_id": 1,
  "file_id": 1,
  "chunk_index": 0,
  "page": 8,
  "chapter": "2.1 技术发展",
  "section_path": "2.1 技术发展",
  "content_type": "body",
  "year_labels": "2026",
  "priority": 1
}
```

## 检索策略

系统使用 Hybrid Search：

- BM25：适合命中年份、频段、型号、术语、章节名等关键词。
- 向量检索：适合语义相近的自然语言问题。
- 多路查询扩展：综合型问题会生成多个检索 query，提升跨章节召回覆盖。
- 结果合并去重后，会根据正文优先级、年份匹配和相关度进行排序。

## 普通聊天与知识库问答隔离

系统不会在所有问题中强行注入知识库内容。

```text
普通独立问题 -> 只走普通对话
追问问题 -> 使用最近历史理解指代
知识库问题 -> 检索知识库并动态注入 RAG Prompt
图片附件问题 -> 跳过 RAG，直接走多模态识图
生图请求 -> 由模型判断后走图片生成接口
```

这样可以同时支持普通聊天和知识库问答，避免无关知识库内容污染普通回答。

## 图片与附件

图片附件和知识库文件是分离的：

```text
知识库文件
  -> /api/file/upload
  -> knowledge_file
  -> 文档解析 / 切片 / Embedding / Chroma

聊天图片附件
  -> /api/attachment/upload
  -> chat_attachment
  -> 仅用于当前聊天的多模态输入
  -> 不进入知识库列表
  -> 不参与 RAG 检索
```

当前支持的图片附件类型：

```text
png, jpg, jpeg, webp, gif
```

## 图片生成

图片生成不依赖前端手动切换按钮。后端会先让聊天模型判断当前问题是否需要生成图片：

```text
用户输入
 ↓
Image Router 判断 image / chat
 ↓
image -> 使用生图模型调用 /images/generations
chat  -> 普通聊天或 RAG
```

模型配置中：

- `Chat Model`：用于普通聊天、RAG、查询重写、Router 判断。
- `生图模型`：可选，仅在需要生成图片时使用。

如果未配置生图模型，系统会返回明确提示，不会拿聊天模型硬试图片接口。

图片接口如果返回 base64，后端会保存成图片文件，并只把短 URL 写入数据库，避免 MySQL `TEXT` 字段被超长 base64 撑爆。

## RAG 监控

系统会记录每次 RAG 调用信息：

- 原始问题
- 改写后的查询
- 是否使用知识库
- 问题类型
- 扩展查询
- 召回数量
- 引用来源
- 质量预判

前端知识库页面可以查看最近 RAG 记录，用于分析回答质量问题。

## 目录结构

```text
backend/
  app/
    api/          FastAPI 路由
    crud/         数据库读写
    database/     MySQL / Chroma 配置与模型
    redisUtils/   Redis 上下文缓存
    services/     聊天、RAG、文件、Embedding 等业务逻辑
  migrations/     Alembic 数据库迁移

frontEnd/
  web-chat/
    src/
      api/          前端接口定义
      assets/       样式文件
      components/   聊天、侧边栏、知识库、设置等组件
      pages/        页面入口
      types/        TypeScript 类型
```

## 核心接口

### 认证

- `POST /api/auth/register`：注册
- `POST /api/auth/login`：登录
- `GET /api/auth/me`：获取当前用户信息

### 会话

- `GET /api/conversation`：获取会话列表
- `POST /api/conversation`：创建会话
- `GET /api/conversation/{conversation_id}/messages`：获取会话消息

### 聊天

- `POST /api/chat`：流式聊天接口

### 文件知识库

- `POST /api/file/upload`：上传知识库文件
- `GET /api/file`：获取知识库文件列表
- `GET /api/file/{file_id}/preview`：预览文件
- `POST /api/file/{file_id}/reindex`：重新索引文件
- `DELETE /api/file/{file_id}`：删除文件和对应向量

### 聊天附件

- `POST /api/attachment/upload`：上传聊天图片附件，不进入知识库

### 模型配置

- `GET /api/settings/model`：获取当前模型配置状态
- `GET /api/settings/models`：获取模型配置列表
- `POST /api/settings/model`：新增模型配置
- `PUT /api/settings/model/{config_id}`：更新模型配置
- `POST /api/settings/model/{config_id}/default`：切换当前使用模型
- `DELETE /api/settings/model/{config_id}`：删除指定模型配置
- `DELETE /api/settings/model`：删除当前模型配置

### RAG 监控

- `GET /api/rag-trace`：获取最近 RAG 调用记录

## 本地运行

### 后端

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端默认地址：

```text
http://localhost:8000
```

### 前端

```bash
cd frontEnd/web-chat
npm install
npm run dev
```

前端默认地址：

```text
http://localhost:5173
```

## 环境变量

后端 `backend/.env` 示例：

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/ai_chat
REDIS_URL=redis://localhost:6379/0

SECRET_KEY=change-me
MODEL_CONFIG_SECRET=change-me

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

CHROMA_PATH=./chroma
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh
EMBEDDING_LOCAL_ONLY=false

# 可选：生成图片文件保存目录
GENERATED_IMAGE_DIR=./generated_images
```

前端生产构建可配置：

```env
VITE_API_BASE_URL=/api
```

## Docker 部署

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

服务说明：

- `frontend`：Nginx 托管前端静态资源，并反向代理 `/api`
- `backend`：FastAPI 服务
- `mysql`：业务数据库
- `redis`：上下文缓存
- `chroma`：通过后端挂载目录持久化向量数据

## 注意事项

- 新的语义切片和 metadata 只会应用到新上传或重新索引的文件。
- 如果更新了切片逻辑，已有知识库文件需要执行重新索引。
- 如果部署环境无法访问 HuggingFace，可以将 embedding 模型下载到本地并挂载到容器内。
- 用户模型配置当前支持 OpenAI 兼容协议。
- 如果某个模型只支持 Responses API，而不支持 Chat Completions，需要后端额外适配 Responses API 后才能使用。
- 图片生成依赖服务商支持 `/images/generations`，并且需要填写对应的生图模型名称。
