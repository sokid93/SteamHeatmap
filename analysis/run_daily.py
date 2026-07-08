"""Daily job entrypoint (walking skeleton: one hardcoded game, one language).

Requires SUPABASE_DB_URL in the environment. Run from analysis/:
    .venv/Scripts/python.exe run_daily.py
"""

import os
import sys
from pathlib import Path

from steamheatmap.pipeline import run_pipeline
from steamheatmap.postgres_writer import PostgresWriter
from steamheatmap.region_mapping import region_for_language
from steamheatmap.steam_client import RequestsSteamClient

# Walking-skeleton hardcoded seed (replaced by real top-N fetch in issue #3)
TRACKED_GAMES = {730: "Counter-Strike 2"}
LANGUAGE_CODES = ["english"]


def main() -> int:
    connection_string = os.environ.get("SUPABASE_DB_URL")
    if not connection_string:
        print("SUPABASE_DB_URL is not set", file=sys.stderr)
        return 1

    writer = PostgresWriter(connection_string)
    writer.apply_schema((Path(__file__).parent / "schema.sql").read_text())

    for app_id, name in TRACKED_GAMES.items():
        writer.upsert_game(app_id, name)
    for code in LANGUAGE_CODES:
        writer.upsert_region(region_for_language(code))

    run_pipeline(
        RequestsSteamClient(),
        writer,
        app_ids=list(TRACKED_GAMES.keys()),
        language_codes=LANGUAGE_CODES,
    )
    print("Pipeline run complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
