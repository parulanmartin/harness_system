import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from harness.config import Config

class OpenRouterClient:
    """
    Client for OpenRouter API (https://openrouter.ai).
    Uses standard library urllib to avoid requiring heavy third-party dependencies.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()

    def complete(self, prompt: str, system_prompt: str = "") -> str:
        """
        Sends a completion request to OpenRouter for the configured model.
        Returns the text response content.
        """
        api_key = self.config.openrouter_api_key
        if not api_key:
            # Return graceful mock response if API key is not configured yet
            return (
                f"[MOCK OPENROUTER RESPONSE - Model: {self.config.llm_model}]\n"
                f"Prompt received: {prompt[:100]}...\n"
                "Please configure OPENROUTER_API_KEY in your .env file to enable live completions."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.config.llm_model,
            "messages": messages,
            "temperature": self.config.llm_temperature,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if self.config.openrouter_site_url:
            headers["HTTP-Referer"] = self.config.openrouter_site_url
        if self.config.openrouter_app_name:
            headers["X-Title"] = self.config.openrouter_app_name

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=self.config.openrouter_base_url + "/chat/completions",
            data=data,
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
                choices = body.get("choices", [])
                if choices:
                    return choices[0]["message"]["content"]
                raise ValueError("OpenRouter API returned no completion choices.")
        except urllib.error.HTTPError as err:
            error_body = err.read().decode("utf-8")
            raise RuntimeError(f"OpenRouter API request failed [{err.code}]: {error_body}") from err
        except urllib.error.URLError as err:
            raise RuntimeError(f"Failed to connect to OpenRouter endpoint: {err.reason}") from err
