# 项目开发规则

## 项目简介

FlowAI — 开源 LLMOps 平台，基于 LangChain/LangGraph 可视化构建、调试和部署 AI Agent 应用。

## 技术栈

后端:
- Python 3.10
- Flask 3.1.3
- SQLAlchemy 2.0.49
- PostgreSQL 15
- Redis 6
- Celery 5.6.3
- LangChain / LangGraph
- Weaviate (向量数据库)
- injector (依赖注入)

前端:
- Vue 3 + TypeScript
- Vite 6
- Pinia (状态管理)
- Arco Design Vue (UI 组件库)
- Tailwind CSS
- Vue Flow (工作流可视化编辑器)

## 项目结构

```
api/
  app/http/          # 应用工厂、DI 模块
  config/            # 配置
  internal/
    core/            # 核心业务逻辑 (包括agent定义, 工作流, 知识库检索, 工具调用, 模型封装等核心功能)
    handler/         # 控制器层 (包含后端的所有接口)
    service/         # 服务层 (包括业务层的service代码，真正实现业务逻辑的层级)
    model/           # SQLAlchemy ORM 模型
    schema/          # 请求/响应 Schema (Marshmallow + WTForms)
    entity/          # 枚举和常量
    router/          # 路由注册
    middleware/      # 认证中间件 (JWT / API Key)
    migration/       # Alembic 数据库迁移
    extension/       # Flask 扩展初始化
    exception/       # 自定义异常
    task/            # Celery 异步任务
  pkg/               # 公共工具包 (response, paginator, password, oauth)
  test/              # 测试

ui/src/
  models/            # TypeScript 类型定义
  services/          # API 调用层
  hooks/             # Composition API hooks
  stores/            # Pinia store
  views/             # 页面组件 (按功能模块划分)
  components/        # 公共组件
  utils/             # 工具函数
  router/            # 路由配置
```

## 编码规范

### 通用

- 优先修改现有代码，不要创建重复功能
- 文件名使用 snake_case，类名使用 PascalCase
- 修改代码前必须：1) 阅读相关代码 2) 分析影响范围 3) 给出修改方案，不要直接修改

### 后端

- **分层架构**: Handler → Service → Model，职责严格分离
- Handler 只负责参数接收和校验，业务逻辑放在 Service 层
- 使用 `@inject` + `@dataclass` 进行依赖注入，禁止直接实例化依赖
- 数据库操作使用 `auto_commit()` 上下文管理器处理事务
- 请求校验使用 Flask-WTF `FlaskForm`
- 响应序列化使用 Marshmallow `Schema`
- 命名规范：
  - Handler: `{domain}_handler.py`
  - Service: `{domain}_service.py`
  - Schema: `{domain}_schema.py`，请求结构用 `*Req`命名，响应结构用 `*Resp`命名
  - Model: 单数名词，如 `app.py`
  - Entity: `{domain}_entity.py`

### 前端

- **三层架构**: models/{domain}.ts → services/{domain}.ts → hooks/use-{domain}.ts
- 使用 Composition API (setup script)，不使用 Options API
- 使用 Arco Design Vue 组件库
- 使用 Tailwind CSS 写样式，不写自定义 CSS
- HTTP 请求统一封装在 `utils/request.ts`
- 分页使用 `BasePaginatorRequest` / `BasePaginatorResponse<T>` 标准类型

## API 规范

统一返回格式：

```json
{
  "code": "success",
  "message": "操作成功",
  "data": {}
}
```

code 可选值: `success`, `fail`, `not_found`, `unauthorized`, `forbidden`, `validate_error`

对应工具函数: `success_json(data)`, `success_message(msg)`, `validate_error_json(errors)`, `not_found_error(msg)`, `unauthorized_error()`, `forbidden_error()`

## 数据库规范

- 表名使用小写下划线
- 主键统一使用 UUID，通过 `server_default=text("uuid_generate_v4()")` 生成
- 时间字段统一使用 `created_at` / `updated_at`
- 使用 JSONB 存储灵活配置字段
- 数据库迁移使用 Alembic (Flask-Migrate)，不要手动改表

## 认证规范

- 主蓝图 (`llmops`) 使用 JWT Bearer Token 认证
- OpenAPI 蓝图使用 API Key 认证
- 登录保护使用 `@login_required` 装饰器

## 禁止事项

- 禁止在 Handler 中直接操作数据库
- 禁止绕过依赖注入手动创建 Service 实例
- 禁止跳过 Schema 校验直接使用请求参数
- 禁止手动执行 SQL，使用 SQLAlchemy ORM
- 禁止在代码中硬编码密钥、Token 等敏感信息
- 禁止未经评估就修改 core/ 下的 agent、workflow、retriever 等核心模块
