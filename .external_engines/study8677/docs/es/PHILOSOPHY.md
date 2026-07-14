# Filosofía del Proyecto

## Tesis del Producto

Las herramientas de programación con IA funcionan mejor cuando pueden hacer
preguntas enfocadas contra un modelo fresco del repositorio, en lugar de releer
todo el árbol para cada tarea. Antigravity es esa capa de conocimiento del
repositorio.

El flujo principal es deliberadamente pequeño:

1. `ag-refresh` escanea el workspace y construye artefactos en `.antigravity/`.
2. `ag-ask` enruta una pregunta al contexto de módulo correcto y responde con
   evidencia de código.
3. Plugins, comandos CLI, archivos de contexto y MCP exponen la misma capa de
   conocimiento a distintos entornos de desarrollo con IA.

## Principios de Diseño

### Una Base de Conocimiento, Muchos Hosts

El directorio generado `.antigravity/` es estado portable del proyecto. Claude
Code, Codex CLI, Cursor, Windsurf, Gemini CLI, Cline, Aider y otros hosts deben
beneficiarse del mismo modelo del repositorio, sin sistemas de contexto
separados.

### Respuestas Fundamentadas Sobre Contexto Amplio

Los prompts enormes son fáciles de crear y difíciles de confiar. Antigravity
prefiere respuestas enrutadas con conocimiento por módulo, rutas de archivo,
evidencia de líneas y contexto de grafo opcional.

### Los Plugins Son Canales de Entrega

Claude Code y Codex CLI reciben comandos slash nativos porque es la forma más
ergonómica para esos hosts. El límite del producto sigue siendo el motor de
conocimiento: `ag-refresh`, `ag-ask` y los artefactos que producen.

### Compatibilidad Sin Bloqueo de Proveedor

`ag-setup` escribe un contrato `.env` OpenAI-compatible: `OPENAI_BASE_URL`,
`OPENAI_API_KEY` y `OPENAI_MODEL`. Esto cubre OpenAI, DeepSeek, Groq, DashScope,
NVIDIA NIM, Ollama y proveedores personalizados sin convertir ningún modelo en
el valor por defecto del producto.

## Qué Pertenece Aquí

Antigravity debe priorizar:

- mejor escaneo de repositorios y agrupación de módulos
- Q&A más fundamentado y validación de evidencia
- rutas de instalación claras para usuarios de plugins nativos
- contratos estables de CLI y MCP
- documentación y checks de CI que mantengan consistente la historia del producto

Funcionalidades que conviertan el repositorio en un agent OS genérico, gestor de
workflows o scaffold no relacionado deben mantenerse separadas salvo que mejoren
claramente el motor de conocimiento del repositorio.

---

**Siguiente:** [Guía de Inicio Rápido](QUICK_START.md) | [Índice Completo](README.md)
