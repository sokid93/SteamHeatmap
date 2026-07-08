import psycopg2

from steamheatmap.pipeline import RegionGameScore
from steamheatmap.region_mapping import Region


class PostgresWriter:
    """Supabase/Postgres writer. Untested by design (ADR-008) — the seam
    faked in tests is the RegionScoreWriter protocol, not this class."""

    def __init__(self, connection_string: str):
        self._connection_string = connection_string

    def apply_schema(self, schema_sql: str) -> None:
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            cur.execute(schema_sql)

    def upsert_game(self, app_id: int, name: str) -> None:
        with psycopg2.connect(self._connection_string) as conn, conn.cursor() as cur:
            cur.execute(
                """insert into games (app_id, name) values (%s, %s)
                   on conflict (app_id) do update set name = excluded.name""",
                (app_id, name),
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

    def write_region_scores(self, rows: list[RegionGameScore]) -> None:
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
