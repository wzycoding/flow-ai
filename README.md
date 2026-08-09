<div align="center">
<img src="ui/public/logo.png" alt="FlowAI Logo" width="180" />


# FlowAI

### 可视化构建 LLM 工作流

一个基于 LangChain / LangGraph 的开源 LLMOps 平台，用于构建、调试和部署 AI Agent 应用。

</div>

---

## FlowAI 是什么？

FlowAI 帮助你**零代码**创建 AI 应用。通过可视化界面构建 Agent、接入 RAG 知识库、连接外部工具、编排复杂工作流 —— 一切开箱即用。

- **快速构建** — 拖拽式 DAG 工作流编辑器，所见即所得
- **知识库** — 上传文档，自动索引，支持向量 + 关键词混合检索
- **工具集成** — 内置工具（Google、DuckDuckGo、DALL-E、高德地图等）+ 自定义 API 工具（OpenAPI Schema）
- **多模型支持** — GPT、小米 MiMo、Moonshot、Ollama、通义千问、文心一言等
- **一键发布** — 将 Agent 发布为独立 Web App，即刻上线
- **全链路可观测** — Token 用量、费用追踪、Agent 推理过程逐步记录

> [!TIP]
> 想直接上手？跳转到 [快速开始](#快速开始)。

---

## 目录

<details>
<summary><kbd>展开目录</kbd></summary>

- [FlowAI 是什么？](#flowai-是什么)
- [快速开始](#快速开始)
- [功能特性](#功能特性)
  - [应用工作台](#应用工作台)
  - [工作流编辑器](#工作流编辑器)
  - [知识库（RAG）](#知识库rag)
  - [工具生态](#工具生态)
  - [多模型支持](#多模型支持)
  - [可观测性](#可观测性)
- [技术栈](#技术栈)
- [部署](#部署)

---

## 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.10+（本地开发后端）
- Node.js 18+（本地开发前端）

### Docker 一键部署（推荐）

```bash
git clone https://github.com/your-org/flowai.git
cd flowai

# 复制并编辑环境变量
cp .env.example .env

# 启动所有服务
docker compose up -d
```

打开 **http://localhost:5000** 即可开始使用。

### 本地开发

<details>
<summary><kbd>后端</kbd></summary>

```bash
cd api
pip install -r requirements.txt

# 启动基础设施（可用 docker compose 只启动中间件）
docker compose up -d postgres redis weaviate

# 启动 Flask 服务
flask run
```

</details>

<details>
<summary><kbd>前端</kbd></summary>

```bash
cd ui
yarn install
yarn dev
```

</details>

---

## 功能特性

### 应用工作台

完整的 AI 应用生命周期管理 —— 创建、配置、调试、发布、版本回退。每个应用可独立绑定模型、提示词、工具、知识库和工作流。

- 实时流式调试聊天（SSE）
- 版本历史，支持一键回退
- 安全审核：关键词过滤、输入/输出审核
- 发布为独立 Web App，支持 Token 分享

### 工作流编辑器

基于有向无环图（DAG）的可视化编排，无需写代码即可构建复杂 AI 流水线。

| 节点类型 | 说明 |
|---|---|
| LLM | 调用已配置的语言模型 |
| 工具 | 调用内置工具或自定义 API 工具 |
| 知识库检索 | 基于 RAG 从知识库中查询信息 |
| 代码节点 | 执行自定义 Python/JS 逻辑 |
| HTTP 请求 | 调用外部 API |
| 模板转换 | Jinja 风格模板格式化数据 |

- 内置图校验：连通性检测、环路检测（Kahn 算法）
- 调试模式：逐步运行整个流水线，查看每个节点的输出

### 知识库（RAG）

将文档变成可查询的知识库，支持混合检索。

1. **上传** — 支持 PDF、Word、TXT 等格式
2. **自动索引** — 通过 Celery 异步执行：解析、分段、向量化
3. **检索** — 语义检索 / 全文检索 / 混合检索，自由选择
4. **命中测试** — 上线前预览检索效果

### 工具生态

**内置工具** — 开箱即用：

| 提供者 | 能力 |
|---|---|
| Google 搜索 | 网络搜索 |
| DuckDuckGo | 隐私优先的网络搜索 |
| DALL-E | 文生图 |
| 高德地图 | 天气、IP 查询 |
| 维基百科 | 知识检索 |
| 时间工具 | 时间日期工具 |

**自定义 API 工具** — 粘贴 OpenAPI Schema 即可定义自己的工具，支持自定义请求头和认证。

### 多模型支持

自由接入你偏好的 LLM 提供者：

OpenAI | 小米 MiMo | Moonshot | Ollama | 通义千问 | 文心一言

> 每个模型可独立配置 Base URL 和 API Key —— 带你自己的 Key 即可使用。

### 可观测性

- **Token 与费用追踪** — 每条消息的 Token 用量和预估费用
- **Agent 推理日志** — 逐步记录每次工具调用和 LLM 决策
- **会话管理** — 置顶、重命名、整理对话历史
- **应用统计** — 所有已发布应用的使用数据分析

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Flask, Python |
| 数据库 | PostgreSQL |
| 向量数据库 | Weaviate（+ FAISS） |
| 缓存 / 消息队列 | Redis |
| 异步任务 | Celery |
| AI 框架 | LangChain, LangGraph |
| 前端 | Vue 3, Tailwind CSS, Arco Design |

---

## 部署

启动容器

```bash
docker compose up -d
```

构建+启动（需要重新构建代码）

```
docker compose --env-file /data/llmops/env/.env up -d --build
```

停止容器（保留容器）

```
docker compose stop
```

停止+删除

```
docker compose down
```

全部重启

```
docker compose restart
```

重启单个服务

```
docker compose restart llmops-api
docker compose restart llmops-celery
docker compose restart llmops-redis
docker compose restart llmops-db
docker compose restart llmops-nginx
```

查看状态

```
docker compose ps
```

查看日志

```
docker compose logs -f
```

看某个服务日志

```
docker compose logs -f llmops-api
```

看最近100行日志

```
docker compose logs -f --tail=100 llmops-api
```

