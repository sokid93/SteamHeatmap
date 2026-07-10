"""Daily job entrypoint: track the current top-N most-played games.

Requires SUPABASE_DB_URL in the environment. Run from analysis/:
    .venv/Scripts/python.exe run_daily.py
"""

import os
import sys
from pathlib import Path

from steamheatmap.pipeline import fetch_tracked_games, run_pipeline
from steamheatmap.postgres_writer import PostgresWriter
from steamheatmap.region_mapping import region_for_language
from steamheatmap.steam_client import RequestsSteamClient

TOP_N_GAMES = 100  # ADR-005: track the current top ~100 by concurrent players
LANGUAGE_CODES = ["english"]  # expands to the full language set in issue #4


def main() -> int:
    connection_string = os.environ.get("SUPABASE_DB_URL")
    if not connection_string:
        print("SUPABASE_DB_URL is not set", file=sys.stderr)
        return 1

    writer = PostgresWriter(connection_string)
    writer.apply_schema((Path(__file__).parent / "schema.sql").read_text())

    steam = RequestsSteamClient()
    tracked_games = fetch_tracked_games(steam, limit=TOP_N_GAMES)
    print(f"Tracking {len(tracked_games)} most-played games.")

    for game in tracked_games:
        writer.upsert_game(game.app_id, game.name)
    for code in LANGUAGE_CODES:
        writer.upsert_region(region_for_language(code))

    run_pipeline(
        steam,
        writer,
        app_ids=[game.app_id for game in tracked_games],
        language_codes=LANGUAGE_CODES,
    )
    print("Pipeline run complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
