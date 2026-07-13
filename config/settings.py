"""Environment-backed settings, loaded once and shared as a singleton.

Every other module should read configuration through `settings`, never
via `os.getenv(...)` directly - this keeps the .env contract in one place.
"""
import os

from dotenv import load_dotenv

from config.constants import DEFAULT_API_URL

load_dotenv()


class Settings:
    def __init__(self):
        # --- Collector ---
        self.API_URL = os.getenv("API_URL", DEFAULT_API_URL)
        self.API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "20"))
        self.API_RETRY_ATTEMPTS = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
        self.API_RETRY_DELAY_SECONDS = int(os.getenv("API_RETRY_DELAY_SECONDS", "3"))

        # --- Database ---
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = int(os.getenv("DB_PORT", "5432"))
        self.DB_NAME = os.getenv("DB_NAME", "job_market")
        self.DB_USER = os.getenv("DB_USER", "postgres")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "")

        # --- Logging ---
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
