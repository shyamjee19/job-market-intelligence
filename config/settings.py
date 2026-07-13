"""Environment-backed settings, loaded once and shared as a singleton.

Every other module should read configuration through `settings`, never
via `os.getenv(...)` directly - this keeps the .env contract in one place.
"""
import os

from dotenv import load_dotenv

from config.constants import DEFAULT_ARBEITNOW_API_URL, DEFAULT_REMOTEOK_API_URL

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

        # Not wired up yet - present so adding the source later is a
        # config-only change. See collector/sources/base.py for how to add it.
        self.ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
        self.ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
        self.JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")
        self.USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY")

        # --- Database ---
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = int(os.getenv("DB_PORT", "5432"))
        self.DB_NAME = os.getenv("DB_NAME", "job_market")
        self.DB_USER = os.getenv("DB_USER", "postgres")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "")

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


settings = Settings()
