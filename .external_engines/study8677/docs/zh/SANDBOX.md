# Sandbox 代码执行

## 概览

sandbox 模块为 Agent 生成的 Python 代码提供可配置执行环境。

- `local`（默认）：零配置 subprocess 执行。
- `microsandbox`（显式 opt-in）：通过 Microsandbox server 执行。
- `e2b`（未来）：占位 runtime。

默认口径是服务可信本地 workspace 的开发便利。local sandbox 不是执行不可信代码的隔离边界。

## 快速开始

### 本地执行（默认）

```python
from antigravity_engine.sandbox.factory import get_sandbox

sandbox = get_sandbox()
result = sandbox.execute(code="print(2 + 2)", language="python", timeout=30)
print(result.stdout)
```

### Microsandbox 执行（Opt-In）

先安装并启动 Microsandbox server：

```bash
curl -sSL https://get.microsandbox.dev | sh
msb server start --dev
```

再选择 Microsandbox runtime：

```bash
export SANDBOX_TYPE=microsandbox
export MSB_SERVER_URL=http://127.0.0.1:5555
export MSB_IMAGE=microsandbox/python
```

`Dockerfile.sandbox` 只是外部 sandbox 实验的辅助镜像，不由 `SANDBOX_TYPE` 选择。

## 配置

### 核心变量

| Variable | Default | Description |
|----------|---------|-------------|
| `SANDBOX_TYPE` | `local` | Runtime：`local`、`microsandbox`、`e2b`（未来） |
| `SANDBOX_TIMEOUT_SEC` | `30` | 最大执行时间（秒） |
| `SANDBOX_MAX_OUTPUT_KB` | `10` | stdout/stderr 截断前最大大小（KB） |

### Microsandbox 变量

仅在 `SANDBOX_TYPE=microsandbox` 时使用。

| Variable | Default | Description |
|----------|---------|-------------|
| `MSB_SERVER_URL` | `http://127.0.0.1:5555` | Microsandbox server URL |
| `MSB_API_KEY` | 空 | 可选认证 token |
| `MSB_IMAGE` | `microsandbox/python` | sandbox 启动镜像 |
| `MSB_CPU_LIMIT` | `1.0` | CPU hint |
| `MSB_MEMORY_MB` | `512` | 内存 hint（MB） |
| `MSB_START_TIMEOUT_SEC` | `30` | 启动 timeout |

## 安全模型

### Local Sandbox

- 只有进程级隔离。
- 适合快速、本地、零配置开发。
- 只适合可信本地 workspace。
- 不适合不可信 workload 或多用户隔离。

### Microsandbox

- 在 Microsandbox 管理的隔离 runtime 中执行代码。
- 比本地 subprocess 提供更强边界。
- 需要 Microsandbox server 可用。

如果请求 `SANDBOX_TYPE=microsandbox` 或 `SANDBOX_TYPE=e2b`，但对应 runtime
不可用，engine 会输出 warning 并降级到本地执行，避免开发流程直接失败。这个降级仍应视为可信本地执行。

## 代码使用

```python
from antigravity_engine.sandbox.factory import get_sandbox

sandbox = get_sandbox()
result = sandbox.execute(code="print('Hello')", language="python", timeout=30)

print(result.exit_code)
print(result.stdout)
print(result.stderr)
print(result.meta)
```

## 故障排查

### "Microsandbox server unavailable"

```bash
msb server start --dev
export MSB_SERVER_URL=http://127.0.0.1:5555
```

### Timeout

```bash
export SANDBOX_TIMEOUT_SEC=120
```

## 测试

```bash
pytest engine/tests/test_local_sandbox.py engine/tests/test_microsandbox_sandbox.py engine/tests/test_factory.py -v
```
