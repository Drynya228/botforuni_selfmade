import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    """Read environment variable stripping whitespace."""

    return (os.getenv(name) or default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    BOT_TOKEN: str = field(default_factory=lambda: _env("BOT_TOKEN"))
    WEBHOOK_URL: str = field(default_factory=lambda: _env("WEBHOOK_URL"))
    DATABASE_URL: str = field(default_factory=lambda: _env("DATABASE_URL"))
    REDIS_URL: str = field(
        default_factory=lambda: (
            _env("REDIS_URL")
            or _env("REDIS_TLS_URL")
            or "redis://localhost:6379/0"
        )
    )
    TIMEZONE: str = field(default_factory=lambda: _env("TIMEZONE", "Europe/Moscow"))
    ASR_ENABLED: bool = field(default_factory=lambda: _env_bool("ASR_ENABLED", True))
    OCR_ENABLED: bool = field(default_factory=lambda: _env_bool("OCR_ENABLED", True))
    EMBEDDINGS_PROVIDER: str = field(
        default_factory=lambda: _env("EMBEDDINGS_PROVIDER", "dummy")
    )
    OPENAI_API_KEY: str | None = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    EMBEDDING_MODEL: str = field(
        default_factory=lambda: _env("EMBEDDING_MODEL", "text-embedding-3-large")
    )
    LLM_PROVIDER: str = field(default_factory=lambda: _env("LLM_PROVIDER", "dummy"))
    LLM_MODEL: str = field(default_factory=lambda: _env("LLM_MODEL", "gpt-4o-mini"))
    MASK_PII: bool = field(default_factory=lambda: _env_bool("MASK_PII", False))
    OWNER_ID: int = field(
        default_factory=lambda: int(_env("OWNER_ID", "597976714") or "597976714")
    )
    OWNER_IDS: str = field(default_factory=lambda: _env("OWNER_IDS"))


cfg = Settings()


def load_owner_ids(settings: Settings | None = None) -> set[int]:
    """Return a normalized set of Telegram owner IDs."""

    settings = settings or cfg
    owners: set[int] = set()

    if settings.OWNER_ID:
        owners.add(settings.OWNER_ID)

    if settings.OWNER_IDS:
        for raw_id in settings.OWNER_IDS.split(","):
            raw_id = raw_id.strip()
            if not raw_id:
                continue
            try:
                owners.add(int(raw_id))
            except ValueError:
                continue

    return owners


class OwnerConfig:
    """Wrapper that exposes the resolved owner ID set."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.owners = load_owner_ids(settings)
