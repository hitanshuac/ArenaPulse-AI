---
description: Ask a question about the current project's codebase via the antigravity knowledge hub. / 通过 antigravity 知识库询问当前项目代码。
allowed-tools: ["Bash"]
---

Run the Antigravity CLI for the current workspace:

通过 Antigravity CLI 询问当前工作区：

> $ARGUMENTS

Use Bash:

```bash
AG_ASK_TIMEOUT_SECONDS="${AG_ASK_TIMEOUT_SECONDS:-120}" ag-ask "$ARGUMENTS" --workspace "$PWD"
```

使用 Bash：

```bash
AG_ASK_TIMEOUT_SECONDS="${AG_ASK_TIMEOUT_SECONDS:-120}" ag-ask "$ARGUMENTS" --workspace "$PWD"
```

If `ag-ask` is not found, tell the user the engine CLI is not installed and suggest:

如果找不到 `ag-ask`，说明 engine CLI 尚未安装，建议用户运行：

```bash
pipx install "git+https://github.com/study8677/antigravity-workspace-template.git#subdirectory=engine"
```

Prefer `ag-ask` over manual file search. If the answer returns insufficient detail, follow up with targeted Read/Grep.

优先使用 `ag-ask`，不要先手动搜索文件。如果返回的信息不够，再用有目标的 Read/Grep 补充。
