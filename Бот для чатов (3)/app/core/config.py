from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    BOT_TOKEN: str = ""
    WEBHOOK_URL: str = ""
    DATABASE_URL: str
    REDIS_URL: str

    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str = "files"

    TIMEZONE: str = "Europe/Moscow"
    ASR_ENABLED: bool = True
    OCR_ENABLED: bool = True

    EMBEDDINGS_PROVIDER: str = "dummy"  # or openai
    OPENAI_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    LLM_PROVIDER: str = "dummy"  # or openai
    LLM_MODEL: str = "gpt-4o-mini"
    MASK_PII: bool = False
    OWNER_IDS: str | None = None

cfg = Settings()

class OwnerConfig(BaseModel):
    owners: set[int] = set(int(x) for x in (cfg.OWNER_IDS.split(",") if cfg.OWNER_IDS else []) if x)