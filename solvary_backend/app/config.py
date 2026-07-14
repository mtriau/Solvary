from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_name: str = "Solvary"
    debug: bool = False
    environment: str = "dev"  # "dev" | "production" — production fail-fasts on unsafe config
    api_prefix: str = "/api"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    # Google OIDC sign-in; empty = feature disabled
    google_client_id: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]
    database_url: str = "sqlite+aiosqlite:///./solvary.db"
    use_mock_db: bool = False
    # Tests set this: fresh connection per checkout, so pytest's per-test
    # event loops never share a pooled (loop-bound) asyncpg/aiosqlite conn
    db_null_pool: bool = False

    # Execution provider: "mock", "piston"
    execution_provider: str = "mock"
    piston_base_url: str = "http://localhost:2000"
    execution_max_code_bytes: int = 64_000
    execution_default_time_limit_s: float = 5.0
    execution_default_memory_kb: int = 256_000
    execution_user_concurrency: int = 2  # concurrent jobs per user
    execution_user_rate_per_min: int = 30

    # Realtime collaboration backplane: "memory", "redis"
    realtime_backplane: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    ws_snapshot_interval_updates: int = 200  # compact snapshot every N updates
    ws_max_message_bytes: int = 1_000_000

    # LLM provider for the AI assistant: "mock", "openai", "anthropic"
    llm_provider: str = "mock"
    llm_base_url: str = "http://localhost:8001/v1"  # vLLM / OpenAI-compatible endpoint
    llm_api_key: str = "no-key"  # "no-key" for local vLLM, real key for cloud APIs
    llm_model: str = "local-model"  # model name — vLLM uses the path you served
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7
    llm_system_prompt: str = "You are the Solvary assistant, a helpful coding tutor."


@lru_cache
def get_settings() -> Settings:
    return Settings()
