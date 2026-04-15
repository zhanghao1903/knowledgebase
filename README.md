# 📚 知识库系统 / Knowledge Base

一个小而完整的知识库系统原型，支持文档上传、解析、切块、向量化、检索与问答（RAG）。

## 🎯 项目目标

构建一个可部署、可演示的知识库系统，体现对 RAG 产品、后端系统设计、数据建模和检索流程的工程理解。

### 核心能力

- 📄 文档上传与管理（PDF / TXT / DOCX）
- 🔄 文档版本管理
- ✂️ 文本解析与切块
- 🧮 向量化（Embedding）
- 🔍 相似度检索召回
- 💬 基于检索结果的问答（RAG）
- ⚙️ 任务状态管理
- 🐳 Docker Compose 一键部署

## 🏗️ 技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 异步、自动 Swagger 文档 |
| 数据库 | PostgreSQL + pgvector | 关系型 + 向量能力统一 |
| ORM | SQLAlchemy 2.0 (async) | 异步数据库操作 |
| 迁移工具 | Alembic | 数据库版本管理 |
| 文件存储 | 本地目录 | 开发阶段简化 |
| 容器化 | Docker Compose | 一键启动所有服务 |

## 📁 项目结构

```
knowledgebase/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py             # 配置管理
│   ├── database.py           # 数据库连接
│   ├── models/               # SQLAlchemy 数据模型
│   │   ├── knowledge_base.py # 知识库表
│   │   ├── document.py       # 文档 & 版本表
│   │   ├── chunk.py          # 切块表（含向量字段）
│   │   └── task.py           # 任务表
│   ├── schemas/              # Pydantic 请求/响应模型
│   ├── routers/              # API 路由
│   ├── services/             # 业务逻辑层
│   └── core/                 # 异常、工具
├── alembic/                  # 数据库迁移
├── scripts/                  # 工具脚本
├── storage/                  # 文件存储目录
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🗃️ 数据模型

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  knowledge_base  │     │   kb_document    │     │ kb_document_ver  │
│──────────────────│     │──────────────────│     │──────────────────│
│ id (PK)          │◄──┐ │ id (PK)          │◄──┐ │ id (PK)          │
│ name             │   └─│ knowledge_base_id│   └─│ document_id      │
│ description      │     │ filename         │     │ version_number   │
│ document_count   │     │ file_type        │     │ file_path        │
│ created_at       │     │ file_size        │     │ file_size        │
│ updated_at       │     │ file_path        │     │ created_at       │
└──────────────────┘     │ status           │     └──────────────────┘
                         │ current_version  │
                         │ chunk_count      │     ┌──────────────────┐
                         │ error_message    │     │     kb_chunk     │
                         │ created_at       │     │──────────────────│
                         │ updated_at       │  ┌──│ document_id      │
                         └──────────────────┘  │  │ id (PK)          │
                              │                │  │ version_number   │
                              └────────────────┘  │ content          │
                                                  │ chunk_index      │
                         ┌──────────────────┐     │ page_number      │
                         │      task        │     │ metadata (JSONB) │
                         │──────────────────│     │ embedding (vec)  │
                         │ id (PK)          │     │ created_at       │
                         │ document_id (FK) │     └──────────────────┘
                         │ task_type        │
                         │ status           │
                         │ error_message    │
                         │ created_at       │
                         │ updated_at       │
                         │ completed_at     │
                         └──────────────────┘
```

## 🚀 快速启动

### Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/zhanghao1903/knowledgebase.git
cd knowledgebase

# 一键启动
docker compose up --build

# 访问 API 文档
# http://localhost:8000/docs
```

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 中的数据库连接等配置

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --port 8000
```

## 📡 API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/knowledge-bases` | 创建知识库 |
| `GET` | `/api/v1/knowledge-bases` | 知识库列表 |
| `GET` | `/api/v1/knowledge-bases/{id}` | 知识库详情 |
| `PATCH` | `/api/v1/knowledge-bases/{id}` | 更新知识库 |
| `DELETE` | `/api/v1/knowledge-bases/{id}` | 删除知识库 |
| `POST` | `/api/v1/knowledge-bases/{id}/documents` | 上传文档 |
| `GET` | `/api/v1/knowledge-bases/{id}/documents` | 文档列表 |
| `GET` | `/api/v1/documents/{id}` | 文档详情 |
| `GET` | `/api/v1/documents/{id}/versions` | 文档版本列表 |
| `DELETE` | `/api/v1/documents/{id}` | 删除文档 |
| `GET` | `/api/v1/tasks/{id}` | 查询任务状态 |
| `GET` | `/api/v1/tasks` | 任务列表 |
| `GET` | `/health` | 健康检查 |

完整 API 文档请访问: `http://localhost:8000/docs`

## 📋 开发阶段

- [x] **阶段 1**: 系统骨架 — 项目结构、数据库建模、基础 API、Docker 配置
- [ ] **阶段 2**: 文档入库链路 — 文件解析、切块、向量化、任务流转
- [ ] **阶段 3**: 检索问答 — 相似度检索、Prompt 构建、LLM 回答、引用返回
- [ ] **阶段 4**: 完善表现 — 版本管理优化、错误处理、架构图、演示准备

## 🔮 后续规划

- 混合检索（BM25 + Vector）
- Rerank 重排序
- OCR 支持
- 网页链接导入
- 对话历史记忆
- 多用户支持

## 📄 License

MIT
