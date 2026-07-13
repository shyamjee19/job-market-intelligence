from etl.extract import extract_latest_raw_jobs
from etl.load import load_jobs
from etl.transform import transform_jobs
from utils.logger import logger


def run_pipeline() -> int:
    """Extract the latest raw snapshot, transform it, and upsert it into
    Postgres. Returns the number of records loaded."""
    logger.info("ETL pipeline starting...")

    raw_jobs = extract_latest_raw_jobs()
    clean_jobs = transform_jobs(raw_jobs)
    loaded = load_jobs(clean_jobs)

    logger.info("ETL pipeline finished - %d records loaded.", loaded)
    return loaded


if __name__ == "__main__":
    run_pipeline()
