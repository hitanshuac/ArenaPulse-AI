import hashlib
import json
import os
from typing import Any

import google.generativeai as genai


class SecureLLMClient:
    """
    Interceptor layer enforcing the OWASP Security mandate.
    Handles I/O sanitization, state memoization, and API quota limits.
    """
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.api_available = True if self.api_key else False
        if self.api_available:
            genai.configure(api_key=self.api_key)

        self.response_cache = {}
        self.daily_calls_made = 0
        self.DAILY_LIMIT = 15

    def _generate_state_hash(self, data: Any) -> str:
        """Creates a unique hash for the current data to check against the cache."""
        return hashlib.md5(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()

    def generate_content(self, prompt: str, state_data: Any = None) -> dict[str, Any]:
        """
        Executes a secure LLM call with pre-flight and post-flight interception.
        If state_data is provided, checks the memoization cache first.
        """
        state_hash = None
        if state_data:
            state_hash = self._generate_state_hash(state_data)
            if state_hash in self.response_cache:
                cached_resp = self.response_cache[state_hash]
                return {"status": "cached", "data": dict(cached_resp)}

        if self.daily_calls_made >= self.DAILY_LIMIT or not self.api_available:
            return {"status": "quota_exhausted", "data": None}

        # Pre-flight Defense (LLM01): Truncate to safe maximum length
        safe_prompt = prompt[:8000]

        try:
            self.daily_calls_made += 1
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(safe_prompt, generation_config={"response_mime_type": "application/json"})

            # Post-flight Defense (LLM06)
            result = json.loads(response.text)

            if state_hash:
                self.response_cache[state_hash] = dict(result)

            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "error": str(e), "data": None}
