import os


def evaluate_response_quality(system_prompt: str, user_query: str, ai_response: str) -> int:
    """
    Simulates calling an LLM API to evaluate the quality of a response on a scale of 1-5.
    1 = Poor/Hallucination/Rude
    5 = Excellent/Helpful/Aligned
    """
    api_key = os.getenv("EVAL_API_KEY")

    # Graceful degradation for CI/CD environments without an API key
    if not api_key:
        # We perform a basic deterministic mock check instead to simulate the LLM
        if "idiot" in ai_response.lower() or "wrong" in ai_response.lower():
            return 1
        elif "help" in ai_response.lower() or "here is" in ai_response.lower():
            return 5
        return 3

    # In a real environment, this would be an HTTP request to OpenAI/HuggingFace
    # e.g., requests.post("https://api.openai.com/v1/chat/completions", ...)

    # Simulated API Logic
    if "error" in ai_response.lower() or len(ai_response) < 5:
        return 1
    return 5
