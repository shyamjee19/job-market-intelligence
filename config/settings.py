"""Environment-backed settings, loaded once and shared as a singleton.

Every other module should read configuration through `settings`, never
via `os.getenv(...)` directly - this keeps the .env contract in one place.
"""
import os
import secrets
import warnings

from dotenv import load_dotenv

from config.constants import (
    DEFAULT_ADZUNA_API_URL,
    DEFAULT_ADZUNA_COUNTRY,
    DEFAULT_ARBEITNOW_API_URL,
    DEFAULT_REMOTEOK_API_URL,
    DEFAULT_USAJOBS_API_URL,
)

load_dotenv()


class Settings:
    def __init__(self):
        # --- Collector: shared HTTP behavior ---
        self.API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "20"))
        self.API_RETRY_ATTEMPTS = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
        self.API_RETRY_DELAY_SECONDS = int(os.getenv("API_RETRY_DELAY_SECONDS", "3"))

        # --- Collector: per-source URLs/keys. New sources add a pair of
        # lines here and a Source implementation in collector/sources/ -
        # nothing else in the pipeline needs to change. ---
        self.REMOTEOK_API_URL = os.getenv("REMOTEOK_API_URL", DEFAULT_REMOTEOK_API_URL)
        self.ARBEITNOW_API_URL = os.getenv("ARBEITNOW_API_URL", DEFAULT_ARBEITNOW_API_URL)

        # Adzuna and USAJobs are wired up (collector/sources/adzuna.py,
        # usajobs.py) but need credentials to actually run - the registry
        # (collector/sources/registry.py) only activates a source once its
        # required settings below are all set, so an empty .env here is
        # safe and just means those two sources sit inactive.
        self.ADZUNA_API_URL = os.getenv("ADZUNA_API_URL", DEFAULT_ADZUNA_API_URL)
        self.ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", DEFAULT_ADZUNA_COUNTRY)
        self.ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
        self.ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

        self.USAJOBS_API_URL = os.getenv("USAJOBS_API_URL", DEFAULT_USAJOBS_API_URL)
        self.USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY")
        # USAJobs requires a contact email as the User-Agent header - see
        # https://developer.usajobs.gov/API-Reference
        self.USAJOBS_EMAIL = os.getenv("USAJOBS_EMAIL")

        # Not wired up yet - present so adding the source later is a
        # config-only change. See collector/sources/base.py for how to add it.
        self.JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")

        # --- Database ---
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = int(os.getenv("DB_PORT", "5432"))
        self.DB_NAME = os.getenv("DB_NAME", "job_market")
        self.DB_USER = os.getenv("DB_USER", "postgres")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "")

        # --- AI module (ai/) ---
        # Which provider actually answers chat/generation requests, and
        # which one turns text into embedding vectors for the RAG chatbot -
        # kept separate because Anthropic has no embeddings API, so
        # "Claude for chat" still needs a real embedding provider.
        self.AI_CHAT_PROVIDER = os.getenv("AI_CHAT_PROVIDER", "openai")
        self.AI_EMBEDDING_PROVIDER = os.getenv("AI_EMBEDDING_PROVIDER", "openai")

        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        self.ANTHROPIC_CHAT_MODEL = os.getenv("ANTHROPIC_CHAT_MODEL", "claude-3-5-sonnet-20241022")

        self.AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
        self.AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        self.AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        self.AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1")

        # RAG vector store: "memory" needs no account and is the default -
        # ai/vectorstore/registry.py switches to Pinecone once its settings
        # below are all set, same conditional-activation pattern as
        # collector/sources/registry.py.
        self.VECTOR_STORE_PROVIDER = os.getenv("VECTOR_STORE_PROVIDER", "memory")
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        self.PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "jobpulse-jobs")

        self.AI_RATE_LIMIT_PER_MINUTE = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "20"))
        self.AI_MAX_MESSAGE_LENGTH = int(os.getenv("AI_MAX_MESSAGE_LENGTH", "2000"))

        # --- Auth (auth/) ---
        # No dev-default password/OAuth secret is ever generated - those
        # must come from real credentials. JWT_SECRET_KEY is the one
        # exception: it's generated per-process if unset so local dev
        # works out of the box, but that means tokens stop validating on
        # every restart and MUST be set to a fixed value outside local dev.
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or self._dev_jwt_secret()
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))

        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
        self.GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")

        self.GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
        self.GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
        self.GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/v1/auth/github/callback")

        # Base URL of the frontend - used to build links that go into
        # emails (password reset) and OAuth redirects.
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

        # Where the frontend lands after an OAuth redirect, with a one-time
        # code appended - see auth/router.py.
        self.OAUTH_FRONTEND_REDIRECT_URL = os.getenv("OAUTH_FRONTEND_REDIRECT_URL", f"{self.FRONTEND_URL}/oauth/callback")

        # "Remember me" unchecked at login issues a refresh token that
        # expires much sooner than the normal 30 days - see auth/router.py.
        self.JWT_REMEMBER_ME_OFF_REFRESH_DAYS = int(os.getenv("JWT_REMEMBER_ME_OFF_REFRESH_DAYS", "1"))

        # How long a password-reset link stays valid.
        self.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30"))

        self.RESUME_UPLOAD_DIR = os.getenv("RESUME_UPLOAD_DIR", "data/resumes")
        self.RESUME_MAX_SIZE_MB = int(os.getenv("RESUME_MAX_SIZE_MB", "5"))

        self.API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
        self.AUTH_RATE_LIMIT_PER_MINUTE = int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "10"))

        # --- Caching / background jobs ---
        # Unset by default - database/cache.py and jobs/celery_app.py fall
        # back to in-memory caching and FastAPI BackgroundTasks respectively
        # when this is empty, same "degrade gracefully, don't crash"
        # pattern as every other optional integration in this project.
        self.REDIS_URL = os.getenv("REDIS_URL")
        self.CACHE_DEFAULT_TTL_SECONDS = int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", "60"))

        # --- Email (utils/email.py) ---
        # Unset by default - notifications get logged to notification_log
        # and the app log instead of actually sent, per the "build the
        # logic now, wire real sending later" call made for this project.
        self.SMTP_HOST = os.getenv("SMTP_HOST")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USER = os.getenv("SMTP_USER")
        self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
        self.EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "noreply@jobpulse.local")

        # --- Snowflake (optional - only used if these are set) ---
        self.SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
        self.SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
        self.SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
        self.SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "JMI_WH")
        self.SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "JMI_DB")
        self.SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "CURATED")
        self.SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")

        # --- Logging ---
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @staticmethod
    def _dev_jwt_secret() -> str:
        warnings.warn(
            "JWT_SECRET_KEY is not set - using a random per-process secret. "
            "Tokens issued before a restart will stop validating, and this "
            "is NOT safe outside local development. Set JWT_SECRET_KEY in .env.",
            stacklevel=2,
        )
        return secrets.token_urlsafe(32)


settings = Settings()
