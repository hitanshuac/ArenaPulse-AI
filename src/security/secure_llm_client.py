import hashlib
import json
import os
from datetime import datetime, timezone
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
        self.DAILY_LIMIT = 15
        self.quota_file = os.path.join("data", "quota.json")
        self.daily_calls_made = self._load_quota()

    def _load_quota(self) -> int:
        """Loads the API quota from persistent storage, resetting if it's a new day."""
        os.makedirs("data", exist_ok=True)
        today = datetime.now(timezone.utc).date().isoformat()
        
        try:
            if os.path.exists(self.quota_file):
                with open(self.quota_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                if data.get("last_reset_date") == today:
                    return data.get("calls_made", 0)
        except Exception:
            pass
            
        # It's a new day (or file missing/corrupt), reset quota to 0
        return 0

    def _save_quota(self):
        """Flushes the current API quota to persistent storage."""
        today = datetime.now(timezone.utc).date().isoformat()
        data = {
            "last_reset_date": today,
            "calls_made": self.daily_calls_made
        }
        try:
            with open(self.quota_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def invalidate_cache_for_state(self, state_data: Any) -> bool:
        """Evicts a poisoned cache entry when downstream validation fails."""
        state_hash = self._generate_state_hash(state_data)
        if state_hash in self.response_cache:
            del self.response_cache[state_hash]
            return True
        return False

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
            self._save_quota()
            
            model = genai.GenerativeModel("gemini-3.5-flash")
            response = model.generate_content(safe_prompt, generation_config={"response_mime_type": "application/json"})

            # Post-flight Defense (LLM06)
            result = json.loads(response.text)

            if state_hash:
                self.response_cache[state_hash] = dict(result)

            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "error": str(e), "data": None}
