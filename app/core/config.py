from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+asyncpg://radar:radar@postgres:5432/radar"
    redis_url: str = "redis://redis:6379/0"
    eth_rpc_url: str = ""
    base_rpc_url: str = ""
    bsc_rpc_url: str = ""
    poll_interval: int = 3
    confirmations: int = 2
    log_batch_blocks: int = 100
    rpc_timeout: int = 20
    whale_usd_threshold: float = 10000
    signal_min_score: int = 70
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_min_score: int = 90
    dexscreener_enabled: bool = True
    api_keys: str = "demo-key"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def api_key_set(self):
        return {x.strip() for x in self.api_keys.split(",") if x.strip()}

settings = Settings()

# Optional external security provider. Leave blank to run local heuristics only.
try:
    settings.GOPLUS_API_URL
except Exception:
    pass
