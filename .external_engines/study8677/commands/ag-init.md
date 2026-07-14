---
description: Scaffold a new multi-agent repository from the Antigravity template (invokes agent-repo-init skill). / 基于 Antigravity 模板创建新的多智能体仓库。
---

This command scaffolds a new repository from the Antigravity template. It is not required before `/antigravity:ag-refresh`; refresh initializes the current workspace's `.antigravity/` knowledge directory automatically.

本命令用于基于 Antigravity 模板创建一个新仓库。运行 `/antigravity:ag-refresh` 前不需要执行它；refresh 会自动初始化当前工作区的 `.antigravity/` 知识目录。

Invoke the `agent-repo-init` skill. Parse $ARGUMENTS for: project name, destination path, mode (`quick` or `full`). If any are missing, ask before running `${CLAUDE_PLUGIN_ROOT}/skills/agent-repo-init/scripts/init_project.py`.

调用 `agent-repo-init` skill。解析 $ARGUMENTS 中的项目名、目标路径和模式（`quick` 或 `full`）。如果缺少任何参数，先询问用户，再运行 `${CLAUDE_PLUGIN_ROOT}/skills/agent-repo-init/scripts/init_project.py`。
