"""Static, non-secret values shared across the pipeline.

Anything that varies by environment (credentials, hosts, ports) belongs in
config/settings.py instead - this file is for values that never change
between dev/staging/prod.
"""

DEFAULT_API_URL = "https://remoteok.com/api"

RAW_DATA_DIR = "data/raw"
RAW_LATEST_FILENAME = "jobs_latest.json"

LOG_DIR = "logs"
LOG_FILENAME = "job_market_intelligence.log"

JOBS_TABLE = "jobs"

# RemoteOK's feed always returns a metadata record (no "id" field) as the
# first element, followed by the actual job postings.
METADATA_RECORD_INDEX = 0
