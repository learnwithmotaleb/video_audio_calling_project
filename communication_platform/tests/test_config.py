import pytest
from pydantic import ValidationError

from app.core.config import Environment, Settings


def make_settings(**overrides) -> Settings:
    values = {
        "postgres_user": "user",
        "postgres_password": "p@ss/word",
        "postgres_db": "db",
        "redis_password": "redis-secret",
        "livekit_api_key": "key",
        "livekit_api_secret": "livekit-secret",
    }
    return Settings(_env_file=None, **(values | overrides))


def test_cors_origins_are_split_from_a_comma_separated_string():
    settings = make_settings(cors_origins="https://a.test, https://b.test,")
    assert settings.cors_origins == ["https://a.test", "https://b.test"]


def test_database_url_keeps_special_characters_in_the_password():
    url = make_settings().database_url
    assert url.password == "p@ss/word"
    assert url.drivername == "postgresql+asyncpg"


def test_secrets_are_hidden_from_repr():
    assert "redis-secret" not in repr(make_settings())


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"postgres_password": "change-me"}, "POSTGRES_PASSWORD"),
        ({"redis_password": ""}, "REDIS_PASSWORD"),
        ({"livekit_api_secret": "change-me"}, "LIVEKIT_API_SECRET"),
        ({"livekit_public_url": "ws://media.test"}, "LIVEKIT_PUBLIC_URL"),
        ({"cors_origins": "*", "livekit_public_url": "wss://media.test"}, "CORS_ORIGINS"),
    ],
)
def test_production_rejects_unsafe_values(overrides, message):
    with pytest.raises(ValidationError, match=message):
        make_settings(environment=Environment.PRODUCTION, **overrides)


def test_production_accepts_real_secrets():
    settings = make_settings(
        environment=Environment.PRODUCTION, livekit_public_url="wss://media.test"
    )
    assert settings.cors_origins == []


def test_development_allows_placeholder_secrets():
    settings = make_settings(environment=Environment.DEVELOPMENT, postgres_password="change-me")
    assert settings.postgres_password.get_secret_value() == "change-me"
