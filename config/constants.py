"""Static, non-secret values shared across the pipeline.

Anything that varies by environment (credentials, hosts, ports) belongs in
config/settings.py instead - this file is for values that never change
between dev/staging/prod.
"""

DEFAULT_REMOTEOK_API_URL = "https://remoteok.com/api"
DEFAULT_ARBEITNOW_API_URL = "https://arbeitnow.com/api/job-board-api"
DEFAULT_ADZUNA_API_URL = "https://api.adzuna.com/v1/api/jobs"
DEFAULT_ADZUNA_COUNTRY = "us"
DEFAULT_USAJOBS_API_URL = "https://data.usajobs.gov/api/search"

RAW_DATA_DIR = "data/raw"
RAW_LATEST_FILENAME = "jobs_latest.json"

LOG_DIR = "logs"
LOG_FILENAME = "job_market_intelligence.log"

# RemoteOK's feed always returns a metadata record (no "id" field) as the
# first element, followed by the actual job postings.
METADATA_RECORD_INDEX = 0

SOURCE_REMOTEOK = "remoteok"
SOURCE_ARBEITNOW = "arbeitnow"
SOURCE_ADZUNA = "adzuna"
SOURCE_USAJOBS = "usajobs"
