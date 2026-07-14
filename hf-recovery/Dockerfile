FROM ghcr.io/open-webui/open-webui:main

# Configure Open WebUI to connect to the Agentic Application Space
# IMPORTANT: Set this via Hugging Face Space Settings (Variables & Secrets)
# ENV OPENAI_API_BASE_URL="https://your-username-your-space.hf.space/v1"
# OPENAI_API_KEY will be injected securely via Hugging Face Space Secrets

# Disable authentication since the HF Space will be strictly Private
ENV WEBUI_AUTH="False"

# Disable Ollama API to prevent retry storms against broken local endpoints
ENV ENABLE_OLLAMA_API="False"

# Hugging Face Spaces port requirement
ENV PORT=7860
