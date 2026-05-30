# OurAI

**基于 LangGraph 和 Docker 的多智能体自动编程框架。** 将自然语言需求转化为可运行代码，Planner → Coder → Sandbox → Reviewer 状态机工作流，失败时自动进入修复循环。

下文用「八段叙事」说明仓库分层；每段对应一类能力边界，便于导航代码与文档。

---

### 1. `chore: bootstrap repo and dependencies`

**含义**：先把「仓库能拿到手、别人知道怎么跑」这层铺好。  
**通常包含**：忽略规则（不把密钥、缓存、构建垃圾进库）、依赖清单（Python/Node 装什么）、说明文档、若有的话部署/平台脚本（`scripts/`、`.coze`）。  
**叙事作用**：还没有业务代码，只有工程边界和协作约定。

**本仓库**：`requirements.txt` / `pyproject.toml`、`frontend/package.json`、`.env.example`、`scripts/`、`.coze`、本 `readme.md`。

---

### 2. `feat(core): config, logging, state, llm, and routing`

**含义**：把后端「发动机舱」一次立起来——从哪读配置、怎么打日志、工作流共享状态长什么样、怎么连各家 LLM、Planner/Coder 之后往哪条边走路。  
**叙事作用**：其它模块都依赖这层；没有它，后面的 agent 和图无处挂接。

**代码入口**：`src/core/config.py`、`logger.py`、`state.py`、`llm_engine.py`、`routing.py`。

---

### 3. `feat(tools): file tools for planner and coder`

**含义**：实现「智能体怎么碰磁盘」：读、写、改、备份、列目录等，以及 Planner 用的那一套工具子集。  
**叙事作用**：把「模型输出」和「真实文件系统」之间的桥梁搭好，后面四个 agent 才能动手改代码。

**代码入口**：`src/tools/file_tools.py`（含 AST 大文件概要、三层编辑匹配）。

---

### 4. `feat(agents): planner, coder, sandbox, reviewer`

**含义**：四个业务节点本体：计划、改代码、Docker 里跑测、失败时诊断与给修复方向。  
**叙事作用**：多智能体行为都在这一层；此时可以还缺「总装配图」，但每个角色的职责已经写清。

**代码入口**：`src/agents/Planner.py`、`Coder.py`、`Sandbox.py`、`Reviewer.py`。

---

### 5. `feat(graph): LangGraph workflow entrypoint`

**含义**：用 `run.py` 把节点、边、条件路由、工具节点等串成 **可执行的 StateGraph**（CLI/程序入口）。  
**叙事作用**：强调「工作流已经能从头到尾跑一条线」，而不只是四个散文件。

**代码入口**：`run.py`（`route_after_planner` / `route_after_coder` / `route_after_sandbox`）。

---

### 6. `feat(context): context manager, repo map, metrics, recovery`

**含义**：在「能跑」之上加 **规模与可靠性**：长对话怎么压上下文、大文件怎么靠 AST 地图导航、调用与修复循环怎么统计、断路器时怎么打快照恢复。  
**叙事作用**：从 demo 走向可观测、可恢复、可长期跑的任务。

**代码入口**：`src/core/context_manager.py`、`repo_map.py`、`metrics.py`、`recovery.py`。

---

### 7. `feat(server+api+frontend): FastAPI SSE, models, and React UI`

**含义**：把同一套图通过 **HTTP + SSE** 暴露给浏览器；Pydantic 模型规范请求/响应；React 做聊天、指标、文件、配置等页面。  
**叙事作用**：从命令行/脚本驱动变成「产品形态」的 Web 应用。

**代码入口**：`api_server.py`、`src/api/models.py`、`frontend/`（`ChatPage.tsx`、`MetricsPage.tsx`、`FileBrowserPage.tsx`、`ConfigPage.tsx`）。

---

### 8. `test+ci: pytest coverage and GitHub Actions`

**含义**：用自动化测试锁住关键行为（状态、路由、文件工具、上下文、指标、API），并在 CI 里每次推送/PR 跑一遍。  
**叙事作用**：说明项目在迭代后期开始用质量闸门，而不是只堆功能。

**本仓库**：以本地 `pytest`（及 `pyproject.toml` 中 coverage 阈值）为主；可在你的环境中自行接 CI，本仓库不再内置平台侧流水线配置文件。

---

## 工作原理（简图）

```
用户需求 → Planner → Coder ⇄ coder_tools → Sandbox → (失败) Reviewer → Coder … → END
```

**循环**：Sandbox 失败则 Reviewer 分析并让 Coder 修复，直到通过或断路器打快照。

---

## 环境要求

- Python 3.10+
- Docker Desktop（沙箱）
- 至少一家 LLM：OpenAI / Anthropic / Ollama / DeepSeek

## 安装与配置

在**本仓库根目录**执行：

```bash
pip install -r requirements.txt
```

复制 `.env.example` 为 `src/core/.env`，按提供商填入密钥与模型名（见文件内注释）。

## 运行

```bash
# 后端 API（默认 8100，静态资源可带前端 dist）
python api_server.py

# 前端开发（另开终端；Vite 常代理 /api 到后端）
cd frontend && npm install && npm run dev

# LangGraph CLI（run.py 内默认 prompt）
python run.py

# 可选：安装可编辑包后使用控制台入口（与上式等价）
pip install -e .
OurAI
```

课设/批处理模式（若使用）：`python cli.py --help`。

## 常用开发命令

```bash
pytest
pytest --cov=src --cov=api_server --cov=run
ruff check src/ api_server.py run.py
mypy api_server.py run.py src/ --ignore-missing-imports --no-error-summary
```

## REST API（摘要）

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/run` | 启动工作流 |
| `GET` | `/api/run/{thread_id}/events` | SSE 事件 |
| `POST` | `/api/run/{thread_id}/cancel` | 取消 |
| `GET` | `/api/run/{thread_id}/state` | 最终状态 |
| `GET` | `/api/files` / `/api/files/{path}` | 工作区文件 |
| `GET` | `/api/metrics` | 指标 |
| `GET` | `/api/config` | 配置与环境变量摘要 |
| `GET` | `/api/snapshots` / `/api/backups` | 快照与备份 |

## 开源协议


