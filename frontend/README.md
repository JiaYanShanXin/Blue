# OurAI 前端（React + TypeScript + Vite）

与根目录八段叙事中的第 7 段一致：**`feat(server+api+frontend)`** —— 通过浏览器消费同一套 LangGraph 工作流（SSE 事件、聊天、指标、文件、配置）。

## 开发

在后端已启动（例如根目录 `python api_server.py`）的前提下：

```bash
pnpm install
pnpm run dev
```

开发服务器默认代理 `/api` 到本机后端（参见 `vite.config`）。

## 构建

```bash
pnpm run build
```

产物在 `dist/`；生产环境可由根目录 `api_server.py` 作为静态资源挂载。

## 目录提示

- `src/pages/`：各业务页面
- `src/api/`：HTTP/SSE 客户端
- `src/context/`：全局状态
