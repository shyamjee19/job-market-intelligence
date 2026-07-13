"""CLI entrypoint for job-market-intelligence.

Usage:
    python main.py collect    # fetch from the API and save a raw snapshot
    python main.py etl        # transform + load the latest raw snapshot
    python main.py run        # collect, then etl (default)
    python main.py init-db    # create/update the database schema
"""
import argparse
import sys

from collector.fetch_jobs import run as run_collector
from database.connection import init_schema
from etl.pipeline import run_pipeline
from utils.logger import logger


def collect():
    return run_collector()


def etl():
    return run_pipeline()


def run():
    snapshot_path = collect()
    if not snapshot_path:
        logger.warning("Collector returned no data - skipping ETL.")
        return
    etl()


COMMANDS = {
    "collect": collect,
    "etl": etl,
    "run": run,
    "init-db": init_schema,
}


def main():
    parser = argparse.ArgumentParser(description="job-market-intelligence pipeline")
    parser.add_argument("command", choices=COMMANDS.keys(), nargs="?", default="run")
    args = parser.parse_args()

    try:
        COMMANDS[args.command]()
    except Exception:
        logger.exception("Command '%s' failed.", args.command)
        sys.exit(1)


if __name__ == "__main__":
    main()
