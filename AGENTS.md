# OurAI 项目规范

仓库分层用下面八段叙事描述（与 `readme.md`、`CLAUDE.md` 对齐），便于在代码与文档之间对照。

---

### 1. `chore: bootstrap repo and dependencies`

**含义**：先把「仓库能拿到手、别人知道怎么跑」这层铺好。  
**通常包含**：忽略规则（不把密钥、缓存、构建垃圾进库）、依赖清单（Python/Node 装什么）、说明文档、若有的话部署/平台脚本（`scripts/`、`.coze`）。  
**叙事作用**：还没有业务代码，只有工程边界和协作约定。

---

### 2. `feat(core): config, logging, state, llm, and routing`

**含义**：把后端「发动机舱」一次立起来——从哪读配置、怎么打日志、工作流共享状态长什么样、怎么连各家 LLM、Planner/Coder 之后往哪条边走路。  
**叙事作用**：其它模块都依赖这层；没有它，后面的 agent 和图无处挂接。

**入口**：`src/core/config.py`、`logger.py`、`state.py`、`llm_engine.py`、`routing.py`。

---

### 3. `feat(tools): file tools for planner and coder`

**含义**：实现「智能体怎么碰磁盘」：读、写、改、备份、列目录等，以及 Planner 用的那一套工具子集。  
**叙事作用**：把「模型输出」和「真实文件系统」之间的桥梁搭好，后面四个 agent 才能动手改代码。

**入口**：`src/tools/file_tools.py`。

---

### 4. `feat(agents): planner, coder, sandbox, reviewer`

**含义**：四个业务节点本体：计划、改代码、Docker 里跑测、失败时诊断与给修复方向。  
**叙事作用**：多智能体行为都在这一层；此时可以还缺「总装配图」，但每个角色的职责已经写清。

**入口**：`src/agents/Planner.py`、`Coder.py`、`Sandbox.py`、`Reviewer.py`。

---

### 5. `feat(graph): LangGraph workflow entrypoint`

**含义**：用 `run.py` 把节点、边、条件路由、工具节点等串成 **可执行的 StateGraph**（CLI/程序入口）。  
**叙事作用**：强调「工作流已经能从头到尾跑一条线」，而不只是四个散文件。

**入口**：`run.py`。

---

### 6. `feat(context): context manager, repo map, metrics, recovery`

**含义**：在「能跑」之上加 **规模与可靠性**：长对话怎么压上下文、大文件怎么靠 AST 地图导航、调用与修复循环怎么统计、断路器时怎么打快照恢复。  
**叙事作用**：从 demo 走向可观测、可恢复、可长期跑的任务。

**入口**：`src/core/context_manager.py`、`repo_map.py`、`metrics.py`、`recovery.py`。

---

### 7. `feat(server+api+frontend): FastAPI SSE, models, and React UI`

**含义**：把同一套图通过 **HTTP + SSE** 暴露给浏览器；Pydantic 模型规范请求/响应；React 做聊天、指标、文件、配置等页面。  
**叙事作用**：从命令行/脚本驱动变成「产品形态」的 Web 应用。

**入口**：`api_server.py`、`src/api/models.py`、`frontend/`。

---

### 8. `test+ci: pytest coverage and GitHub Actions`

**含义**：用自动化测试锁住关键行为，并在 CI 里每次推送/PR 跑一遍。  
**叙事作用**：说明项目在迭代后期开始用质量闸门，而不是只堆功能。

**本仓库**：本地以 `pytest` 与 `pyproject.toml` 中 coverage 配置为主；平台 CI 由你在部署环境中自行接入。

---

## 目录结构（简）

```
<项目根>/
├── api_server.py
├── run.py
├── cli.py
├── frontend/
├── src/
│   ├── api/
│   ├── agents/
│   ├── core/
│   └── tools/
├── scripts/
├── tests/
└── readme.md / AGENTS.md / CLAUDE.md
```

## 运行与预览

### 开发命令（约定：Python `uv`，Node `pnpm`）

```bash
uv sync
cd <项目根>/frontend && pnpm install && pnpm run dev
cd <项目根> && python api_server.py
```

### 环境配置

- 后端：`src/core/.env`
- 示例：`.env.example`

### Docker

沙箱需要 Docker Desktop。

## Coze 配置

### 根 `.coze`（工作区 `projects/.coze`）

- 平台读取入口；`project_type = "web"`；`preview_enable = "enabled"`；`[subprojects]` 注册本子项目。

### 子项目 `.coze`（本目录 `.coze`）

- `sub_id` 按平台要求固定。
- 预览：`scripts/coze-preview-build.sh`、`scripts/coze-preview-run.sh`
- 部署：`scripts/deploy-build.sh`、`scripts/deploy-run.sh`

### 端口

- 预览/部署验证：`curl http://localhost:5000` 期望 200。
- 本地开发：Vite 常见 3000，后端 API 8100（开发）/ 5000（部署视脚本而定）。

## 用户偏好与长期约束

1. **包管理器**：Python 用 `uv`，Node.js 用 `pnpm`（避免 npm/yarn 混用）。
2. **Python**：>= 3.10。

## 界面主题（当前 v2.0.0-nature）

**主题色**：`#c5eff6`（主背景）、`#e2eff1`（次背景）、`#eef4bc`（强调）。  
**侧栏渐变**：`#5fb3c4` → `#7ec8d9` → `#8dd3e8`；页面背景 `#e8f4f6`。  
近期 UI 调整包括：执行轨迹网格、文件浏览器卡片化、品牌展示名 **OurAI**。

## 常见问题

1. **沙箱失败**：确认 Docker Desktop 已运行。
2. **依赖**：`uv sync` / 前端 `pnpm install`。
3. **端口占用**：部署前检查 5000 等端口是否被占用。
