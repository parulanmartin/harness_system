import os
from dataclasses import dataclass

def _load_dotenv_if_exists():
    """Lightweight .env parser using standard library without external dependencies."""
    env_paths = [".env", os.path.join(os.path.dirname(__file__), "..", ".env")]
    for path in env_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'").strip('"')
                        if k not in os.environ:
                            os.environ[k] = v
            break

@dataclass(frozen=True)
class Config:
    llm_provider: str = "openrouter"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = ""
    openrouter_app_name: str = "Harness Requirements System"
    
    # Specialized Model Routing via OpenRouter
    llm_model_extract: str = "google/gemini-2.5-flash"
    llm_model_semantic: str = "deepseek/deepseek-v4-flash"
    llm_model_detect: str = "deepseek/deepseek-v4-flash"
    
    # Google Sheets & Workspace Configuration
    google_sheets_credentials_path: str = "credentials.json"
    harness_master_sheet_id: str = ""
    harness_drive_folder_id: str = ""
    local_storage_dir: str = "data/projects"
    
    llm_temperature: float = 0.0

    @classmethod
    def from_env(cls) -> "Config":
        _load_dotenv_if_exists()

        default_extract = os.getenv("LLM_MODEL_EXTRACT", "google/gemini-2.5-flash")
        default_semantic = os.getenv("LLM_MODEL_SEMANTIC", "deepseek/deepseek-v4-flash")
        default_detect = os.getenv("LLM_MODEL_DETECT", "deepseek/deepseek-v4-flash")

        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "openrouter").lower(),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", ""),
            openrouter_app_name=os.getenv("OPENROUTER_APP_NAME", "Harness Requirements System"),
            llm_model_extract=default_extract,
            llm_model_semantic=default_semantic,
            llm_model_detect=default_detect,
            google_sheets_credentials_path=os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials.json"),
            harness_master_sheet_id=os.getenv("HARNESS_MASTER_SHEET_ID", ""),
            harness_drive_folder_id=os.getenv("HARNESS_DRIVE_FOLDER_ID", ""),
            local_storage_dir=os.getenv("LOCAL_STORAGE_DIR", "data/projects"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
        )
