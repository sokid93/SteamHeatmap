"""Weekly catalog refresh entrypoint: cache every Steam app's id and name for
full-catalog search reach, independent of the daily review-scoring pipeline.

Requires SUPABASE_DB_URL in the environment. Run from analysis/:
    .venv/Scripts/python.exe refresh_catalog.py
"""

import os
import sys
from pathlib import Path

from steamheatmap.catalog import refresh_catalog
from steamheatmap.postgres_writer import PostgresWriter
from steamheatmap.steam_client import RequestsSteamClient


def main() -> int:
    connection_string = os.environ.get("SUPABASE_DB_URL")
    if not connection_string:
        print("SUPABASE_DB_URL is not set", file=sys.stderr)
        return 1

    writer = PostgresWriter(connection_string)
    writer.apply_schema((Path(__file__).parent / "schema.sql").read_text())

    steam = RequestsSteamClient()
    count = refresh_catalog(steam, writer)
    print(f"Cached {count} Steam apps.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
