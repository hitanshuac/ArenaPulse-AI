FROM ghcr.io/open-webui/open-webui:main

# Fix Hugging Face Spaces permission issue for image uploads
USER root
RUN chown -R 1000:1000 /app/backend/data
USER 1000

ENV ENABLE_OLLAMA_API="False"
ENV WEBUI_AUTH_COOKIE_SAME_SITE="none"
ENV WEBUI_SESSION_COOKIE_SAME_SITE="none"
ENV WEBUI_AUTH_COOKIE_SECURE="true"
ENV WEBUI_SESSION_COOKIE_SECURE="true"

# SRE NOTE: The following variables MUST be injected via Hugging Face Space Settings (Variables & Secrets):
# - OPENAI_API_BASE_URL (URL of your Agentic Application Vision space, e.g., https://...hf.space/v1)
# - OPENAI_API_KEY (Password to your Router space, e.g., sk-antigravity)
# - CORS_ALLOW_ORIGIN (URL of this Open WebUI space)
# - WEBUI_SECRET_KEY (A random alphanumeric hash for session security)
