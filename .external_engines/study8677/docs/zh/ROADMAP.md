# 开发路线图

## 愿景：基于证据的代码库知识层

Antigravity 正收敛为一个可移植的 repository knowledge engine：把 workspace
刷新成 `.antigravity/`，用源码证据回答问题，并通过插件、CLI、MCP 暴露同一份知识。

## 当前状态

| 阶段 | 状态 | 描述 |
|------|------|------|
| 1 Foundation | 完成 | 基础结构、配置、记忆系统 |
| 2 DevOps | 完成 | Docker、CI/CD |
| 3 指令与产物协议 | 完成 | 规则、artifacts、协议 |
| 4 高级记忆 | 完成 | 递归摘要、缓冲管理 |
| 5 工具架构 | 完成 | 通用工具分发、function calling |
| 6 动态发现 | 完成 | 工具/上下文零配置加载 |
| 7 Multi-Agent Swarm | 完成 | Router-Worker 编排 |
| 8 MCP 集成 | 完成 | MCP server / consumer 支持 |
| 9 产品化加固 | 进行中 | 安全边界、可观测、安装与文档契约 |
| 10 Knowledge Hub | 完成 | 代码库刷新、模块知识、路由式问答 |

## Phase 9 重点

- Sandbox：local 可信开发边界、Microsandbox/E2B opt-in、降级 warning。
- Retrieval graph：默认保留开发体验，同时做 secret redaction 与风险说明。
- MCP：保留 opt-in 便利性，明确 `AG_ALLOW_MCP`、环境变量和外部 server 权限风险。
- 安装与文档：保持 `ag-setup -> ag-refresh -> ag-ask` 主线，减少旧入口漂移。
- Contract check：用 CI 检查安装脚本、sandbox 文档、模型默认值和 quick start。

## 使用场景

- 新人理解项目：运行 `ag-refresh` 后用 `ag-ask` 提问，答案带文件证据。
- 多 IDE 协作：Claude Code、Codex CLI、Cursor、Windsurf 等读取同一份 `.antigravity/`。
- 安全发布：公开 repo 对本地可信边界、MCP 权限、retrieval graph 风险有清晰说明。

---

**下一步：** [文档索引](README.md)
