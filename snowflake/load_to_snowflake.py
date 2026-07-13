"""
Loads the curated Parquet output produced by streaming/spark_transform.py
into Snowflake: truncate-and-load STG_JOBS, then run the star-schema merge.

Tracks which Parquet files have already been loaded in a small local
manifest so re-running the loader doesn't reprocess old partitions.
"""
import json
import os
from pathlib import Path

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()

PROCESSED_PATH = Path(os.getenv("PROCESSED_PATH", "data/processed/jobs"))
MANIFEST_PATH = Path(os.getenv("LOAD_MANIFEST_PATH", "data/processed/.loaded_manifest.json"))
MERGE_SQL_PATH = Path(__file__).parent / "merge_star_schema.sql"


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "JMI_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "JMI_DB"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "CURATED"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )


def load_manifest() -> set:
    if not MANIFEST_PATH.exists():
        return set()
    return set(json.loads(MANIFEST_PATH.read_text()))


def save_manifest(loaded_files: set):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(sorted(loaded_files), indent=2))


def find_new_parquet_files(already_loaded: set):
    if not PROCESSED_PATH.exists():
        return []
    all_files = {str(p) for p in PROCESSED_PATH.rglob("*.parquet")}
    return sorted(all_files - already_loaded)


def read_new_records(new_files):
    frames = [pd.read_parquet(f) for f in new_files]
    df = pd.concat(frames, ignore_index=True)

    # Snowflake's write_pandas expects upper-case column names by default.
    df.columns = [c.upper() for c in df.columns]

    # ARRAY columns need to go in as JSON-parsable strings for a VARIANT/ARRAY target.
    if "TAGS" in df.columns:
        df["TAGS"] = df["TAGS"].apply(lambda v: json.dumps(list(v)) if v is not None else "[]")

    return df


def stage_and_merge(conn, df: pd.DataFrame):
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE STG_JOBS")

        # Load into a plain-string staging table first, then INSERT ... SELECT
        # with PARSE_JSON so TAGS lands as a true Snowflake ARRAY.
        write_pandas(conn, df.drop(columns=["TAGS"]), "STG_JOBS_FLAT", auto_create_table=True, overwrite=True)

        cursor.execute(
            """
            INSERT INTO STG_JOBS
            SELECT
                f.JOB_ID, f.COMPANY, f.POSITION, f.LOCATION, f.SALARY_MIN, f.SALARY_MAX,
                f.DATE_POSTED, f.INGESTION_DATE, PARSE_JSON(t.TAGS), f.URL, f.APPLY_URL,
                f.DESCRIPTION, CURRENT_TIMESTAMP()
            FROM STG_JOBS_FLAT f
            JOIN (SELECT ROW_NUMBER() OVER (ORDER BY JOB_ID) AS rn, JOB_ID, TAGS FROM (
                SELECT JOB_ID, TAGS FROM STG_JOBS_FLAT
            )) t ON t.JOB_ID = f.JOB_ID
            """
        )

        for statement in MERGE_SQL_PATH.read_text().split(";"):
            statement = statement.strip()
            if statement and not statement.startswith("--"):
                cursor.execute(statement)

        conn.commit()
    finally:
        cursor.close()


def main():
    already_loaded = load_manifest()
    new_files = find_new_parquet_files(already_loaded)

    if not new_files:
        print("No new processed files to load.")
        return

    print(f"Loading {len(new_files)} new Parquet file(s) into Snowflake...")
    df = read_new_records(new_files)

    conn = get_snowflake_connection()
    try:
        stage_and_merge(conn, df)
    finally:
        conn.close()

    save_manifest(already_loaded | set(new_files))
    print(f"Loaded {len(df)} job records and refreshed the star schema.")


if __name__ == "__main__":
    main()
