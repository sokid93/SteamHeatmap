"""Daily job entrypoint: track the current top-N most-played games.

Requires SUPABASE_DB_URL in the environment. Run from analysis/:
    .venv/Scripts/python.exe run_daily.py
"""

import os
import sys
from pathlib import Path

from steamheatmap.pipeline import fetch_tracked_games, run_pipeline, select_app_ids_to_track
from steamheatmap.postgres_writer import PostgresWriter
from steamheatmap.region_mapping import region_for_language, supported_language_codes
from steamheatmap.steam_client import RequestsSteamClient

# ADR-005: track the current top ~100 by concurrent players.
# Overridable for cheap smoke runs (TOP_N_GAMES=3 keeps it to ~100 API calls).
DEFAULT_TOP_N_GAMES = 100

# ADR-016: a searched game stays in daily rotation this many days since it
# was last relevant (top-100 or searched), same spirit as ADR-013's
# named, revisitable-with-evidence threshold.
RELEVANCE_WINDOW_DAYS = 30

# ADR-016: nothing reads any run but the latest; bounds storage growth.
RUNS_TO_KEEP = 3


def main() -> int:
    connection_string = os.environ.get("SUPABASE_DB_URL")
    if not connection_string:
        print("SUPABASE_DB_URL is not set", file=sys.stderr)
        return 1

    writer = PostgresWriter(connection_string)
    writer.apply_schema((Path(__file__).parent / "schema.sql").read_text())

    top_n = int(os.environ.get("TOP_N_GAMES", DEFAULT_TOP_N_GAMES))
    language_codes = supported_language_codes()

    steam = RequestsSteamClient()
    tracked_games = fetch_tracked_games(steam, limit=top_n)
    top_100_app_ids = [game.app_id for game in tracked_games]
    still_relevant_app_ids = writer.still_relevant_app_ids(window_days=RELEVANCE_WINDOW_DAYS)
    app_ids = select_app_ids_to_track(top_100_app_ids, still_relevant_app_ids)
    print(
        f"Tracking {len(tracked_games)} most-played games plus "
        f"{len(app_ids) - len(top_100_app_ids)} still-relevant searched games, "
        f"across {len(language_codes)} languages."
    )

    for game in tracked_games:
        writer.upsert_game(game.app_id, game.name, game.rank)
    writer.clear_stale_ranks(top_100_app_ids)
    for code in language_codes:
        writer.upsert_region(region_for_language(code))

    run_pipeline(steam, writer, app_ids=app_ids, language_codes=language_codes)
    writer.prune_old_runs(keep=RUNS_TO_KEEP)
    print("Pipeline run complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
