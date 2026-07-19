import gradio as gr
from src.main import app as fastapi_app
import uvicorn

# Dummy Gradio app to pass HF's Gradio SDK health checks
with gr.Blocks() as demo:
    gr.Markdown("# ArenaPulse-AI Backend")
    gr.Markdown("FastAPI is running successfully on Hugging Face Free Tier!")

# Mount the dummy Gradio app onto our real FastAPI app
# We mount it at /gradio so it doesn't interfere with our root (/) which serves index.html
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
