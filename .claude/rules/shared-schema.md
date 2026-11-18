---
paths:
  - "analysis/schema.sql"
  - "analysis/steamheatmap/postgres_writer.py"
  - "web/Infrastructure/Postgres*Repository.cs"
---

# One database schema, two codebases

`analysis/schema.sql` is the only schema definition. Python applies it at the
start of every job; C# never creates tables but reads and writes them. There is
no shared ORM or type system (ADR-005), so a schema change is coordinated by
hand:

| Table | Written by | Read by |
|---|---|---|
| `games` | `postgres_writer.py` (daily), `PostgresOnDemandRepository` (on demand) | `PostgresRankingRepository` |
| `regions` | `postgres_writer.py` | `PostgresRankingRepository` |
| `runs` | `postgres_writer.py` | `PostgresRankingRepository`, `PostgresOnDemandRepository` (latest run id) |
| `region_scores` | `postgres_writer.py`, `PostgresOnDemandRepository` | `PostgresRankingRepository` |
| `region_baselines` | `postgres_writer.py` | `PostgresOnDemandRepository` |
| `steam_apps` | `postgres_writer.py` (weekly) | `PostgresCatalogSearchRepository` |

- Keep `schema.sql` additive and idempotent (`if not exists`); it re-runs on
  every job against the live database.
- When a column is added, renamed or retyped, update every repository in the
  table above that touches it in the same change.
- The on-demand path upserts into the latest run and must never overwrite
  `games.most_played_rank`: only the daily run knows a real rank.
- `PostgresRankingRepository` reads columns by position — keep its `select`
  list and its reader indexes in step.
