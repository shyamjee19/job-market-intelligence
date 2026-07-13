"""CLI entrypoint for job-market-intelligence.

Usage:
    python main.py collect               # fetch every source, save raw snapshots
    python main.py collect --source X    # fetch just source X
    python main.py etl                   # transform + load every source's latest snapshot
    python main.py etl --source X        # transform + load just source X
    python main.py run                   # collect, then etl (default)
    python main.py init-db               # create/update the database schema

Registered sources: see collector/sources/registry.py.
"""
import argparse
import sys

from collector.fetch_jobs import run as run_collector
from database.connection import init_schema
from etl.pipeline import run_pipeline
from utils.logger import logger


def collect(source: str | None = None):
    return run_collector(source)


def etl(source: str | None = None):
    return run_pipeline(source)


def run(source: str | None = None):
    collect(source)
    etl(source)


COMMANDS = {
    "collect": collect,
    "etl": etl,
    "run": run,
    "init-db": lambda source=None: init_schema(),
}


def main():
    parser = argparse.ArgumentParser(description="job-market-intelligence pipeline")
    parser.add_argument("command", choices=COMMANDS.keys(), nargs="?", default="run")
    parser.add_argument("--source", default=None, help="Limit to one registered source (default: all)")
    args = parser.parse_args()

    try:
        COMMANDS[args.command](args.source)
    except Exception:
        logger.exception("Command '%s' failed.", args.command)
        sys.exit(1)


if __name__ == "__main__":
    main()
