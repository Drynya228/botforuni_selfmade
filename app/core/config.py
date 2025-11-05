from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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


def load_owner_ids(settings: Settings = cfg) -> set[int]:
    owners = {597_976_714}
    if settings.OWNER_IDS:
        owners.update(
            int(raw_id.strip())
            for raw_id in settings.OWNER_IDS.split(",")
            if raw_id.strip()
        )
    return owners


class OwnerConfig(BaseModel):
    owners: set[int] = Field(default_factory=load_owner_ids)