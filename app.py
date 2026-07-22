import gradio as gr
from src.main import app as fastapi_app

# Dummy Gradio interface to satisfy the Hugging Face Gradio SDK
demo = gr.Blocks()
with demo:
    gr.Markdown("# ArenaPulse-AI Operations Cockpit")
    gr.Markdown("The system is running on the FastAPI backend. Please navigate to the root path `/` to access the full React dashboard.")

# Mount the dummy Gradio app onto the existing FastAPI application
# We mount it under /gradio so that the root (/) continues to serve our React frontend
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
