from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    environment: str = Field(default="development")
    database_url: str = Field(default="sqlite:///./dev.db")
    redis_url: str = Field(default="redis://redis:6379/0")
    jwt_secret: str = Field(default="dev-secret")
    # Clave separada para refresh tokens (permite revocar rotando sólo esta)
    refresh_jwt_secret: str = Field(default="dev-refresh-secret")
    # Duraciones configurables
    access_token_minutes: int = Field(default=60 * 8)
    refresh_token_minutes: int = Field(default=60 * 24 * 14)  # 14 días
    app_name: str = "OFITEC API"
    version: str = "0.1.0"
    skip_migrations: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
