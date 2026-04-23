# 📚 知识库系统 / Knowledge Base

一个小而完整的知识库系统原型，支持文档上传、解析、切块、向量化、检索与问答（RAG）。

> 能体现对知识库产品、后端系统设计、数据建模、检索流程理解的工程作品。

## 🎯 核心能力

- 📄 文档上传与管理（PDF / TXT / DOCX）
- 🔄 文档版本管理（重新上传自动创建新版本）
- ✂️ 文本解析与切块（滑动窗口，保留原文位置映射）
- 🧮 向量化（Embedding，自动分批处理）
- 🔍 相似度检索召回（pgvector 余弦距离）
- 💬 基于检索结果的问答（RAG，带引用来源）
- ⚙️ 任务状态管理（异步处理，状态可查）
- 🛡️ 统一错误响应格式
- 🐳 Docker Compose 一键部署

---

## 即将推出
- 对URL文档的支持
- 全新界面与交互，更好看的界面，更人性化的交互
## 未来规划
- chunk的优化，对复杂格式文档的更好体验
- 本地embedding的支持

## 🏛️ 系统架构

```mermaid
graph TB
    User([用户]) --> FE[前端 Vue 3 SPA<br/>Nginx]
    FE -->|/api/*| API[FastAPI API Server]

    subgraph "API 层"
        API --> KB[知识库管理]
        API --> DOC[文档管理]
        API --> QA[问答接口]
        API --> TASK[任务查询]
        API --> HEALTH[健康检查]
    end

    subgraph "文档入库流程"
        DOC -->|上传| STORE[文件存储]
        DOC -->|创建任务| WORKER[后台 Worker]
        WORKER -->|1| PARSER[文档解析器<br/>PDF / TXT / DOCX]
        PARSER -->|2| CHUNKER[文本切块器<br/>滑动窗口]
        CHUNKER -->|3| EMB[Embedding 客户端]
        EMB -->|4| PG[(PostgreSQL<br/>+ pgvector)]
    end

    subgraph "检索问答流程 RAG"
        QA -->|query embedding| EMB_Q[Embedding]
        EMB_Q -->|余弦搜索 Top-K| PG
        PG -->|召回 chunks| PROMPT[Prompt 构建<br/>系统指令 + 引用 + 问题]
        PROMPT -->|调用| LLM[LLM<br/>OpenRouter]
        LLM -->|answer + citations| User
    end

    EMB -->|OpenAI 兼容 API| EMB_SVC[Embedding 服务]
    LLM -->|OpenRouter API| LLM_SVC[LLM 服务]
```

---

## 🏗️ 技术选型

| 组件 | 技术 | 选型理由 |
|------|------|----------|
| **前端** | Vue 3 + Vite | 轻量、响应式、Composition API、开发体验好 |
| **前端部署** | Nginx | 静态文件服务 + API 反向代理 |
| 后端框架 | FastAPI | 异步高性能、自动 Swagger 文档、类型安全 |
| 数据库 | PostgreSQL + pgvector | 单库同时处理关系型查询和向量检索，降低运维复杂度 |
| ORM | SQLAlchemy 2.0 (async) | 异步操作、声明式模型、成熟生态 |
| 迁移工具 | Alembic | 数据库版本管理 |
| LLM 服务 | OpenRouter | 聚合多模型，OpenAI 兼容接口，一个 key 访问多种模型 |
| Embedding | OpenAI 兼容 API | 可替换为本地模型 |
| 异步任务 | DB 轮询 Worker | 轻量级，无需 Celery/MQ 依赖 |
| 容器化 | Docker Compose | 一键启动所有服务（前端 + 后端 + DB） |

### 为什么选 Postgres + pgvector 而不是独立向量库？

- ✅ 单一数据库，运维简单，事务一致
- ✅ 关系查询 + 向量检索同一个库中完成
- ✅ 对于原型项目规模足够高效
- ⚠️ 超大规模时可扩展为独立向量库（Milvus/Qdrant）

---

## 📁 项目结构

```
knowledgebase/
├── frontend/                  # 🖥️ Vue 3 前端
│   ├── src/
│   │   ├── main.js            # 应用入口
│   │   ├── App.vue            # 根组件（导航 + Toast）
│   │   ├── router/            # Vue Router
│   │   ├── api/               # API 客户端层
│   │   │   ├── client.js      # fetch 封装（GET/POST/PATCH/DELETE/Upload）
│   │   │   ├── knowledgeBase.js
│   │   │   ├── document.js
│   │   │   ├── task.js
│   │   │   └── qa.js
│   │   ├── views/             # 页面组件
│   │   │   ├── HomeView.vue   # 知识库列表
│   │   │   ├── KBDetailView.vue # 文档管理 + 问答
│   │   │   └── TasksView.vue  # 任务监控
│   │   ├── components/        # 可复用组件
│   │   │   ├── ChatPanel.vue  # 聊天对话
│   │   │   ├── DocUpload.vue  # 拖拽上传
│   │   │   └── StatusBadge.vue
│   │   └── styles/main.css
│   ├── nginx.conf             # Nginx 配置（SPA + API 代理）
│   ├── Dockerfile             # 多阶段构建
│   └── package.json
├── app/                       # 🐍 FastAPI 后端
│   ├── main.py                # 应用入口、CORS、健康检查
│   ├── config.py              # 配置管理
│   ├── database.py            # 数据库连接
│   ├── worker.py              # 后台 Worker
│   ├── models/                # SQLAlchemy 模型
│   ├── schemas/               # Pydantic 模型
│   ├── routers/               # API 路由
│   ├── services/              # 业务逻辑（解析/切块/向量化/检索/问答）
│   └── core/                  # 异常处理
├── tests/                     # 99 个测试
├── alembic/                   # 数据库迁移
├── docker-compose.yml         # 一键启动：DB + API + 前端
├── Dockerfile                 # 后端镜像
└── requirements.txt
```

---

## 🗃️ 数据模型（ER 图）

```mermaid
erDiagram
    knowledge_base ||--o{ kb_document : contains
    kb_document ||--o{ kb_document_version : "has versions"
    kb_document ||--o{ kb_chunk : "split into"
    kb_document ||--o{ task : triggers

    knowledge_base {
        uuid id PK
        string name
        text description
        int document_count
        timestamp created_at
        timestamp updated_at
    }

    kb_document {
        uuid id PK
        uuid knowledge_base_id FK
        string filename
        enum file_type "pdf / txt / docx"
        bigint file_size
        string file_path
        enum status "pending → parsing → chunking → embedding → ready / failed"
        int current_version
        int chunk_count
        text error_message
        timestamp created_at
        timestamp updated_at
    }

    kb_document_version {
        uuid id PK
        uuid document_id FK
        int version_number
        string file_path
        bigint file_size
        timestamp created_at
    }

    kb_chunk {
        uuid id PK
        uuid document_id FK
        int version_number
        text content
        int chunk_index
        int page_number
        jsonb metadata
        vector embedding "1536 维"
        timestamp created_at
    }

    task {
        uuid id PK
        uuid document_id FK
        enum task_type "document_ingest"
        enum status "pending → processing → success / failed"
        text error_message
        timestamp created_at
        timestamp updated_at
        timestamp completed_at
    }
```

---

## 🚀 快速启动

### Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/zhanghao1903/knowledgebase.git
cd knowledgebase

# 配置 API Key
cp .env.example .env
# 编辑 .env，填入 OPENROUTER_API_KEY 和 EMBEDDING_API_KEY

# 一键启动（前端 + 后端 + 数据库）
docker compose up --build

# 访问
# 前端界面:  http://localhost:3500
# API 文档:  http://localhost:8000/docs
# 健康检查:  http://localhost:8000/health
```

### 本地开发

```bash
# 后端
pip install -r requirements.txt
cp .env.example .env    # 编辑配置
alembic upgrade head    # 数据库迁移
uvicorn app.main:app --reload --port 8000

# 前端（另开终端）
cd frontend
npm install
npm run dev             # http://localhost:3500（自动代理 API 到 8000）
```

---

## ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://kb_user:kb_password@localhost:5432/knowledgebase` | 数据库连接 |
| `STORAGE_DIR` | `./storage` | 文件存储目录 |
| **LLM (OpenRouter)** | | |
| `OPENROUTER_API_KEY` | `sk-placeholder` | OpenRouter API Key |
| `LLM_API_URL` | `https://openrouter.ai/api/v1/chat/completions` | LLM 接口地址 |
| `LLM_MODEL` | `openai/gpt-4o-mini` | LLM 模型名 |
| **Embedding** | | |
| `EMBEDDING_API_KEY` | *(空，回退到 OPENROUTER_API_KEY)* | Embedding 专用 Key |
| `EMBEDDING_API_URL` | `https://api.openai.com/v1/embeddings` | Embedding 接口地址 |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | Embedding 模型名 |
| `EMBEDDING_DIMENSION` | `1536` | 向量维度 |
| **切块** | | |
| `CHUNK_SIZE` | `500` | 每个 chunk 最大字符数 |
| `CHUNK_OVERLAP` | `50` | chunk 之间重叠字符数 |
| `RETRIEVAL_TOP_K` | `5` | 检索返回的最相关片段数 |

> 💡 OpenRouter 不提供 Embedding 服务，所以 Embedding 需要独立配置。

---

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/knowledge-bases` | 创建知识库 |
| `GET` | `/api/v1/knowledge-bases` | 知识库列表（分页） |
| `GET` | `/api/v1/knowledge-bases/{id}` | 知识库详情 |
| `PATCH` | `/api/v1/knowledge-bases/{id}` | 更新知识库 |
| `DELETE` | `/api/v1/knowledge-bases/{id}` | 删除知识库 |
| `POST` | `/api/v1/knowledge-bases/{id}/documents` | 上传文档 |
| `GET` | `/api/v1/knowledge-bases/{id}/documents` | 文档列表 |
| `POST` | `/api/v1/knowledge-bases/{id}/query` | **知识库问答（RAG）** |
| `GET` | `/api/v1/documents/{id}` | 文档详情 |
| `GET` | `/api/v1/documents/{id}/versions` | 文档版本列表 |
| `PUT` | `/api/v1/documents/{id}/reupload` | 重新上传（创建新版本） |
| `DELETE` | `/api/v1/documents/{id}` | 删除文档 |
| `GET` | `/api/v1/tasks/{id}` | 查询任务状态 |
| `GET` | `/api/v1/tasks` | 任务列表（支持筛选） |
| `GET` | `/health` | 健康检查（含 DB 状态） |

完整 API 文档请访问: `http://localhost:8000/docs`

---

## 🎬 演示流程

```bash
# 1. 创建知识库
curl -X POST http://localhost:8000/api/v1/knowledge-bases \
  -H "Content-Type: application/json" \
  -d '{"name": "技术文档库", "description": "内部技术文档"}'
# → 返回 kb_id

# 2. 上传文档
curl -X POST http://localhost:8000/api/v1/knowledge-bases/{kb_id}/documents \
  -F "file=@./myfile.pdf"
# → 返回 document + task_id

# 3. 查看任务状态（等待 READY）
curl http://localhost:8000/api/v1/tasks/{task_id}
# → status: "success"

# 4. 提问！
curl -X POST http://localhost:8000/api/v1/knowledge-bases/{kb_id}/query \
  -H "Content-Type: application/json" \
  -d '{"question": "这个系统支持哪些文件格式？"}'
# → answer + citations

# 5. 更新文档（新版本）
curl -X PUT http://localhost:8000/api/v1/documents/{doc_id}/reupload \
  -F "file=@./myfile_v2.pdf"
# → 自动创建 v2，重新切块入库
```

---

## ⚙️ 文档入库流程

```
上传文件 → 保存到磁盘 → 创建 Task(PENDING)
                              ↓
              Worker 拾取任务 → Task: PROCESSING
                              ↓
              解析文本(PDF/TXT/DOCX) → Document: PARSING
                              ↓
              滑动窗口切块 → Document: CHUNKING
                              ↓
              调用 Embedding API → Document: EMBEDDING
                              ↓
              写入 pgvector → Document: READY, Task: SUCCESS
```

### 各模块说明

| 模块 | 文件 | 要点 |
|------|------|------|
| 解析器 | `parser.py` | PDF(pymupdf) / TXT(原生) / DOCX(python-docx)，统一返回 `ParsedDocument(pages=[ParsedPage])` |
| 切块器 | `chunker.py` | 滑动窗口策略，优先在段落/句子/标点边界断开，保留 chunk↔原文字符位置映射 |
| Embedding | `embedding.py` | OpenAI 兼容接口，自动分批（64条/批） |
| 入库管线 | `ingest.py` | 编排 parse→chunk→embed→store，每步更新状态 |
| Worker | `worker.py` | asyncio 后台任务，每 3 秒轮询，随 FastAPI 进程启停 |

---

## 🔍 检索问答流程（RAG）

```
用户提问 → Query Embedding → pgvector 余弦相似度检索 Top-K
                                          ↓
                    构建 Prompt（系统指令 + 编号引用片段 + 用户问题）
                                          ↓
                              调用 LLM 生成回答
                                          ↓
                    返回 answer + citations（内容、文件名、页码、分数）
```

**Prompt 设计要点**:
- 系统指令要求 LLM 仅基于参考资料回答，不编造
- 引用格式 `[1]` `[2]`，方便用户追溯来源
- 参考资料不足时如实说明

---

## 🧪 测试

```bash
pip install -r requirements-test.txt

pytest              # 全部 99 个测试
pytest -m unit      # 单元测试（68 cases，无需 DB）
pytest -m api       # API 端点测试（31 cases，mock 服务层）
pytest -v           # 详细输出
```

### 测试覆盖

| 类别 | 文件 | 数量 | 测试内容 |
|------|------|------|----------|
| 解析器 | `test_parser.py` | 13 | PDF/TXT/DOCX 解析、空文件、中文、类型分派 |
| 切块器 | `test_chunker.py` | 16 | 滑动窗口、重叠、边界断句、多页、边界条件 |
| Prompt | `test_qa_prompt.py` | 5 | 引用格式、空引用、页码空值、编号顺序 |
| Schema | `test_schemas.py` | 10 | 字段校验、长度限制、范围约束 |
| **LLM** | `test_llm.py` | 7 | 请求结构、认证头、温度参数、HTTP 错误、畸形响应 |
| **Embedding** | `test_embedding.py` | 9 | 单文本/多文本、分批(64)、排序、边界、HTTP 错误 |
| **QA 编排** | `test_qa_service.py` | 8 | RAG 全流程、引用格式、空检索、top_k 传递、prompt 内容 |
| KB API | `test_knowledge_base_api.py` | 10 | CRUD、分页、验证 |
| 文档 API | `test_document_api.py` | 9 | 上传、列表、版本、重新上传、删除 |
| 任务 API | `test_task_api.py` | 5 | 详情、列表、状态筛选 |
| QA API | `test_qa_api.py` | 5 | 问答、参数校验、top_k |
| 错误处理 | `test_error_handling.py` | 4 | 404/422/500 统一格式 |

### 测试日志

每次运行自动在 `tests/logs/` 生成 JSON 报告：

```json
{
  "version": "0.1.0",
  "timestamp": "2026-04-19T...",
  "duration_seconds": 1.0,
  "total": 99, "passed": 99, "failed": 0,
  "results": [{"name": "...", "status": "passed", "duration_seconds": 0.007}, ...]
}
```

---

## 🛡️ 错误处理

所有错误返回统一 JSON 格式：

```json
{
  "error": {
    "code": 404,
    "message": "KnowledgeBase with id '...' not found"
  }
}
```

- `404` — 资源不存在
- `422` — 请求参数校验失败（含字段级详情）
- `500` — 服务器内部错误（不泄露堆栈信息）

---

## 🖥️ 前端界面

3 个核心页面，覆盖完整用户流程：

| 页面 | 路由 | 功能 |
|------|------|------|
| **知识库首页** | `/` | 知识库卡片列表、创建/删除知识库 |
| **知识库详情** | `/kb/:id` | 左侧：文档列表 + 上传 + 重传；右侧：问答聊天 |
| **任务监控** | `/tasks` | 任务表格、状态筛选、自动刷新 |

### 前端设计要点

- **组件化**: API 客户端层 → 页面组件 → 可复用 UI 组件
- **拖拽上传**: 支持点击和拖拽两种方式上传文档
- **实时状态**: 文档处理状态自动展示，任务页 5 秒自动刷新
- **聊天式问答**: 对话界面，答案附带引用来源（文件名、页码、相似度）
- **统一错误处理**: API 错误自动 Toast 提示
- **API 代理**: 开发环境 Vite 代理 / 生产环境 Nginx 反向代理，前后端完全解耦

---

## 📋 开发阶段

- [x] **阶段 1**: 系统骨架 — 项目结构、数据库建模、基础 API、Docker 配置
- [x] **阶段 2**: 文档入库链路 — 文件解析、切块、向量化、任务流转
- [x] **阶段 3**: 检索问答 — 相似度检索、Prompt 构建、LLM 回答、引用返回
- [x] **阶段 4**: 测试体系 — 99 个测试、测试日志
- [x] **阶段 5**: 工程完善 — 版本管理、全局错误处理、架构图、环境变量文档
- [x] **阶段 6**: 前端界面 — Vue 3 SPA、知识库管理、文档上传、问答聊天、任务监控

## 🔮 后续规划

- 混合检索（BM25 + Vector）
- Rerank 重排序
- OCR 支持
- 网页链接导入
- 对话历史记忆
- 多用户支持
- 前端界面

## 📄 License

MIT
