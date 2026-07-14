# Ejecución de Código en Sandbox

## Descripción General

El módulo sandbox ofrece entornos configurables para ejecutar código Python
generado por agentes.

- `local` (por defecto): ejecución por subprocess, sin configuración.
- `microsandbox` (opt-in): ejecución mediante un servidor Microsandbox.
- `e2b` (futuro): runtime placeholder.

La postura por defecto prioriza comodidad de desarrollo en un workspace local
confiable. El sandbox local no es una frontera para ejecutar código no confiable.

## Inicio Rápido

### Ejecución Local (Por Defecto)

```python
from antigravity_engine.sandbox.factory import get_sandbox

sandbox = get_sandbox()
result = sandbox.execute(code="print(2 + 2)", language="python", timeout=30)
print(result.stdout)
```

### Ejecución Microsandbox (Opt-In)

Instala e inicia el servidor Microsandbox:

```bash
curl -sSL https://get.microsandbox.dev | sh
msb server start --dev
```

Después usa el runtime Microsandbox:

```bash
export SANDBOX_TYPE=microsandbox
export MSB_SERVER_URL=http://127.0.0.1:5555
export MSB_IMAGE=microsandbox/python
```

`Dockerfile.sandbox` es una imagen auxiliar para experimentos externos. No se
selecciona mediante `SANDBOX_TYPE`.

## Configuración

### Variables Principales

| Variable | Defecto | Descripción |
|----------|---------|-------------|
| `SANDBOX_TYPE` | `local` | Runtime: `local`, `microsandbox`, `e2b` (futuro) |
| `SANDBOX_TIMEOUT_SEC` | `30` | Tiempo máximo de ejecución (segundos) |
| `SANDBOX_MAX_OUTPUT_KB` | `10` | Máximo stdout/stderr antes de truncar (KB) |

### Variables de Microsandbox

Solo se usan cuando `SANDBOX_TYPE=microsandbox`.

| Variable | Defecto | Descripción |
|----------|---------|-------------|
| `MSB_SERVER_URL` | `http://127.0.0.1:5555` | URL del servidor Microsandbox |
| `MSB_API_KEY` | (vacío) | Token opcional de autenticación |
| `MSB_IMAGE` | `microsandbox/python` | Imagen usada al iniciar el sandbox |
| `MSB_CPU_LIMIT` | `1.0` | Sugerencia de CPU |
| `MSB_MEMORY_MB` | `512` | Sugerencia de memoria (MB) |
| `MSB_START_TIMEOUT_SEC` | `30` | Timeout de inicio |

## Modelo de Seguridad

### Sandbox Local

- Solo aislamiento a nivel de proceso.
- Rápido y sin configuración para desarrollo.
- Pensado solo para workspaces locales confiables.
- No es adecuado para workloads no confiables o aislamiento multiusuario.

### Microsandbox

- Ejecuta código en un runtime administrado por Microsandbox.
- Proporciona fronteras más fuertes que un subprocess local.
- Requiere disponibilidad del servidor Microsandbox.

Si se solicita `SANDBOX_TYPE=microsandbox` o `SANDBOX_TYPE=e2b` y el runtime no
está disponible, el engine muestra un warning y vuelve a ejecución local para no
bloquear flujos de desarrollo. Trata esa caída como ejecución local confiable.

## Uso desde Código

```python
from antigravity_engine.sandbox.factory import get_sandbox

sandbox = get_sandbox()
result = sandbox.execute(code="print('Hello')", language="python", timeout=30)

print(result.exit_code)
print(result.stdout)
print(result.stderr)
print(result.meta)
```

## Solución de Problemas

### "Microsandbox server unavailable"

```bash
msb server start --dev
export MSB_SERVER_URL=http://127.0.0.1:5555
```

### Timeouts

```bash
export SANDBOX_TIMEOUT_SEC=120
```

## Pruebas

```bash
pytest engine/tests/test_local_sandbox.py engine/tests/test_microsandbox_sandbox.py engine/tests/test_factory.py -v
```
