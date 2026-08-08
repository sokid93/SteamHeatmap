import psycopg2
from psycopg2.extras import execute_values

from steamheatmap.catalog import CatalogApp
from steamheatmap.pipeline import RegionBaseline, RegionGameScore
from steamheatmap.region_mapping import Region


class PostgresWriter:
    """Supabase/Postgres writer. Untested by design (ADR-008) — the seam
    faked in tests is the RegionScoreWriter protocol, not this class."""

    def __init__(self, connection_string: str):
        self._connection_string = connection_string

    def apply_schema(self, schema_sql: str) -> None:
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            cur.execute(schema_sql)

    def upsert_game(self, app_id: int, name: str, most_played_rank: int) -> None:
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            cur.execute(
                """insert into games (app_id, name, most_played_rank, last_relevant_at)
                   values (%s, %s, %s, now())
                   on conflict (app_id) do update set
                       name = excluded.name,
                       most_played_rank = excluded.most_played_rank,
                       last_relevant_at = excluded.last_relevant_at""",
                (app_id, name, most_played_rank),
            )

    def still_relevant_app_ids(self, window_days: int) -> list[int]:
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            cur.execute(
                """select app_id from games
                   where last_relevant_at >= now() - (%s || ' days')::interval""",
                (window_days,),
            )
            return [row[0] for row in cur.fetchall()]

    def clear_stale_ranks(self, current_top_100_app_ids: list[int]) -> None:
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            cur.execute(
                "update games set most_played_rank = null where not (app_id = any(%s))",
                (current_top_100_app_ids,),
            )

    def upsert_region(self, region: Region) -> None:
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            cur.execute(
                """insert into regions (code, display_name, member_countries, blended)
                   values (%s, %s, %s, %s)
                   on conflict (code) do update set
                       display_name = excluded.display_name,
                       member_countries = excluded.member_countries,
                       blended = excluded.blended""",
                (region.code, region.display_name, region.member_countries, region.blended),
            )

    def write_region_scores(
        self, rows: list[RegionGameScore], baselines: list[RegionBaseline]
    ) -> None:
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            cur.execute("insert into runs default values returning id")
            run_id = cur.fetchone()[0]
            for row in rows:
                cur.execute(
                    """insert into region_scores
                       (run_id, app_id, region_code, total_reviews,
                        in_language_reviews, wilson_adjusted_share, concentration)
                       values (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        run_id,
                        row.app_id,
                        row.region_code,
                        row.total_reviews,
                        row.in_language_reviews,
                        row.wilson_adjusted_share,
                        row.concentration,
                    ),
                )
            for baseline in baselines:
                cur.execute(
                    """insert into region_baselines (run_id, region_code, baseline_share)
                       values (%s, %s, %s)""",
                    (run_id, baseline.region_code, baseline.baseline_share),
                )

    def write_catalog(self, apps: list[CatalogApp]) -> None:
        # steam_apps is 100k+ rows, weekly — bulk upsert, not a per-row loop.
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            execute_values(
                cur,
                """insert into steam_apps (app_id, name) values %s
                   on conflict (app_id) do update set name = excluded.name""",
                [(app.app_id, app.name) for app in apps],
            )

    def prune_old_runs(self, keep: int) -> None:
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            stale_runs = "select id from runs order by id desc offset %s"
            cur.execute(f"delete from region_scores where run_id in ({stale_runs})", (keep,))
            cur.execute(f"delete from region_baselines where run_id in ({stale_runs})", (keep,))
            cur.execute(f"delete from runs where id in ({stale_runs})", (keep,))
