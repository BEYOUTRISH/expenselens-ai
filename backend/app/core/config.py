import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def get_default_database_url() -> str:
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    db_path = Path(upload_dir) / "expenselens.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.absolute()}"


class Settings(BaseSettings):
    app_name: str = "ExpenseLens AI"
    app_version: str = "1.0.0"
    debug: bool = True

    database_url: Optional[str] = None
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-8b-instant"

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 50
    allowed_extensions: list[str] = [".csv", ".xlsx", ".xls"]

    base_currency: str = "INR"
    exchange_rate_source: str = "RBI_REFERENCE"

    secret_key: str = "expenselens-dev-secret-key-change-in-production"
    environment: str = "development"

    cors_origins: str = "*"

    def get_effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return get_default_database_url()

    def get_cors_origins(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_file = str(ENV_FILE) if ENV_FILE.exists() else ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
