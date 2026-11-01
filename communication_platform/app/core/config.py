"""Environment-based application configuration."""

from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


PLACEHOLDER_SECRET = "change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: SecretStr
    redis_db: int = 0

    livekit_host: str = "http://localhost:7880"
    livekit_public_url: str = "ws://localhost:7880"
    livekit_api_key: str
    livekit_api_secret: SecretStr

    health_check_timeout_seconds: float = 2.0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def reject_unsafe_production_values(self) -> Self:
        """Stop a production deployment from booting with development credentials."""
        if self.environment is not Environment.PRODUCTION:
            return self

        problems = []
        for name, secret in (
            ("POSTGRES_PASSWORD", self.postgres_password),
            ("REDIS_PASSWORD", self.redis_password),
            ("LIVEKIT_API_SECRET", self.livekit_api_secret),
        ):
            if secret.get_secret_value() in ("", PLACEHOLDER_SECRET):
                problems.append(f"{name} must be set to a real secret")
        if not self.livekit_public_url.startswith("wss://"):
            problems.append("LIVEKIT_PUBLIC_URL must use wss://")
        if "*" in self.cors_origins:
            problems.append("CORS_ORIGINS must not contain a wildcard")

        if problems:
            raise ValueError("; ".join(problems))
        return self

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
