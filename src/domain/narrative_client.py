import logging
import os
import google.generativeai as genai

logger = logging.getLogger(__name__)

class NarrativeLLMClient:
    """
    An unconstrained LLM client designed specifically for narrative text streaming.
    Bypasses the strict JSON schema required by the core deterministic engine.
    """

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.api_available = True if self.api_key else False
        if self.api_available:
            genai.configure(api_key=self.api_key)

    async def generate_narrative_stream(self, state_summary: str):
        """
        Yields text chunks from the Gemini API using Server-Sent Events (SSE) format.
        Does NOT enforce JSON mime-type.
        """
        if not self.api_available:
            yield "data: [SYSTEM] API Key not configured. Narrative streaming disabled.\n\n"
            return

        prompt = (
            f"You are the AI operations observer for a stadium. The current telemetry data is: {state_summary}. "
            "Write a concise, 2-3 sentence live operational narrative about what is happening right now. "
            "Focus on crowd flow, bottlenecks, and active mitigations. Do not output JSON. Be professional but descriptive."
        )

        try:
            model = genai.GenerativeModel("gemini-3.5-flash")
            response = model.generate_content(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    # Clean the chunk for SSE (replace newlines)
                    clean_text = chunk.text.replace("\n", " ")
                    yield f"data: {clean_text}\n\n"
                    
        except Exception as e:
            logger.error(f"Narrative stream error: {e}")
            yield f"data: [SYSTEM] Error generating narrative: {e}\n\n"
