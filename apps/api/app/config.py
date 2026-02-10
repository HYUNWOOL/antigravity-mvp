from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    creem_api_key: str = ""
    creem_webhook_secret: str = "test_webhook_secret"
    creem_api_base: str = "https://test-api.creem.io"
    frontend_base_url: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
