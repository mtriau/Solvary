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

    # Mock interviews: submissions arriving this long after ends_at still
    # count (network slack); the clock itself is never extended
    interview_grace_s: int = 3

    # Job queue + SSE broker + execution quota: "memory" (single instance)
    # or "redis" (shared across replicas)
    queue_backend: str = "memory"

    # Realtime collaboration backplane: "memory", "redis"
    realtime_backplane: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    ws_snapshot_interval_updates: int = 200  # compact snapshot every N updates
    ws_max_message_bytes: int = 1_000_000

    # LLM provider for the AI assistant (POST /v1/assist/explain):
    #   "mock"   — canned streamed replies, no network (dev/tests)
    #   "openai" — any OpenAI-compatible /chat/completions endpoint: the
    #              matt_llm/serve.py model on :8001, vLLM, OpenAI, Groq…
    llm_provider: str = "mock"
    llm_base_url: str = "http://localhost:8001/v1"
    llm_api_key: str = "no-key"  # "no-key" for local servers, real key for cloud APIs
    llm_model: str = "matt-gpt"  # model name as the server registers it
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7
    llm_system_prompt: str = (
        "You are the Solvary assistant, a patient coding tutor on a competitive-"
        "programming platform. Help the user understand the problem and debug their"
        " own approach. Prefer hints and questions over full solutions; only give a"
        " complete solution when explicitly asked. Be concise and use Markdown."
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
