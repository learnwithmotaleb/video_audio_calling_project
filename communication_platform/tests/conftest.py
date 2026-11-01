import os

# app.main builds the app at import time, so settings must exist before any test imports it.
# Integration runs use the real credentials from .env, which environment variables would override.
if os.getenv("RUN_INTEGRATION") != "1":
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("POSTGRES_USER", "test")
    os.environ.setdefault("POSTGRES_PASSWORD", "test")
    os.environ.setdefault("POSTGRES_DB", "test")
    os.environ.setdefault("REDIS_PASSWORD", "test")
    os.environ.setdefault("LIVEKIT_API_KEY", "test")
    os.environ.setdefault("LIVEKIT_API_SECRET", "test")
