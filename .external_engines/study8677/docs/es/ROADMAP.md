# Hoja de Ruta de Desarrollo

## Visión: Capa de Conocimiento de Repositorios con Evidencia

Antigravity converge hacia un motor portable de conocimiento de repositorios:
refresca un workspace en `.antigravity/`, responde preguntas con evidencia de
código y expone la misma capa mediante plugins, CLI y MCP.

## Estado Actual

| Fase | Estado | Descripción |
|------|--------|-------------|
| 1 Foundation | Completa | Estructura base, configuración, memoria |
| 2 DevOps | Completa | Docker, CI/CD |
| 3 Protocolos | Completa | Reglas, artifacts, contratos de trabajo |
| 4 Memoria Avanzada | Completa | Resumización recursiva y buffers |
| 5 Arquitectura de Herramientas | Completa | Dispatch genérico y function calling |
| 6 Descubrimiento Dinámico | Completa | Herramientas y contexto zero-config |
| 7 Multi-Agent Swarm | Completa | Orquestación Router-Worker |
| 8 MCP Integration | Completa | Soporte MCP server / consumer |
| 9 Endurecimiento de Producto | En progreso | Fronteras de seguridad, observabilidad, docs e instalación |
| 10 Knowledge Hub | Completa | Refresh del codebase, conocimiento modular y Q&A enrutado |

## Foco de Fase 9

- Sandbox: frontera local confiable, opt-in a Microsandbox/E2B y warnings de fallback.
- Retrieval graph: mantener experiencia de desarrollo con redacción de secretos y documentación de riesgos.
- MCP: conservar comodidad opt-in y aclarar `AG_ALLOW_MCP`, entorno y permisos de servidores externos.
- Instalación y documentación: sostener la línea `ag-setup -> ag-refresh -> ag-ask`.
- Contract checks: verificar scripts de instalación, docs de sandbox, modelo por defecto y quick starts.

## Casos de Uso

- Onboarding: ejecutar `ag-refresh` y preguntar con `ag-ask`, recibiendo evidencia de archivos.
- Colaboración multi-IDE: Claude Code, Codex CLI, Cursor y otros usan la misma `.antigravity/`.
- Publicación segura: el repo documenta límites locales confiables, MCP y riesgos del retrieval graph.

---

**Siguiente:** [Índice Completo](README.md)
