import unittest
from harness.config import Config
from harness.llm_client import OpenRouterClient

class TestOpenRouterClient(unittest.TestCase):

    def test_mock_fallback_when_no_key(self):
        cfg = Config(openrouter_api_key="")
        client = OpenRouterClient(config=cfg)
        response = client.complete("Test prompt", system_prompt="Test system")
        self.assertIn("MOCK OPENROUTER RESPONSE", response)
        self.assertIn(cfg.llm_model, response)

    def test_config_model_override(self):
        cfg = Config(openrouter_api_key="", llm_model="google/gemini-2.5-flash")
        client = OpenRouterClient(config=cfg)
        response = client.complete("Hello")
        self.assertIn("google/gemini-2.5-flash", response)

if __name__ == "__main__":
    unittest.main()
