# analysis/ — Python batch jobs

Two scheduled jobs write everything the web app reads. Neither is called by the
web app; they share only the database (ADR-005).

| Entrypoint | Workflow | Schedule | Needs |
|---|---|---|---|
| `run_daily.py` | `daily-pipeline.yml` | Daily 06:30 UTC | `SUPABASE_DB_URL` |
| `refresh_catalog.py` | `weekly-catalog-refresh.yml` | Sundays 06:00 UTC | `SUPABASE_DB_URL`, `STEAM_API_KEY` |

Both apply `schema.sql` first; it is idempotent (`create … if not exists`,
`add column if not exists`), so schema changes must stay additive and
re-runnable. The tables are shared with `web/` — see
`.claude/rules/shared-schema.md`.

## Daily run, in order (`run_daily.py`)

1. Fetch the top-N most-played games (`DEFAULT_TOP_N_GAMES = 100`) and their
   names; upsert them with their rank, and clear the rank of every game no
   longer in today's top-N.
2. Add still-relevant searched games: anything whose `last_relevant_at` falls
   inside `RELEVANCE_WINDOW_DAYS = 30` (ADR-011). `select_app_ids_to_track`
   unions the two lists.
3. `run_pipeline`: total review count per game, then one count per game per
   language for all 30 review languages. Zero-review games are dropped from
   scoring *and* baseline. Each region gets a baseline from every remaining
   game; only games with `MIN_REVIEWS_TO_RANK = 50` in-language reviews are
   ranked (ADR-009). Rows and baselines are written under a new run.
4. Prune to the `RUNS_TO_KEEP = 3` most recent runs.

## Modules

- `pipeline.py` — orchestration, the `SteamClient` protocol (the seam faked in
  tests), `MIN_REVIEWS_TO_RANK`.
- `scoring.py` — Wilson lower bound (z for 95%), region baseline, concentration.
  Ported to C# — see `.claude/rules/scoring-parity.md`.
- `region_mapping.py` — the 30 language codes and their regions (ADR-002).
  Region code = language code everywhere.
- `steam_client.py` — `RequestsSteamClient`, the real HTTP client. Untested by
  design (ADR-006). Retries 429/5xx with backoff, and raises
  `UnexpectedSteamResponse` when a response isn't JSON (retired endpoints
  often still answer 200 with HTML). Error messages must never include the
  request URL: for the catalog call it carries the API key.
- `postgres_writer.py` — every write; untested by design.
- `catalog.py` — the weekly catalog refresh, behind its own small protocols.

## Steam usage

Endpoint details and their history: `docs/steam-web-api.md`.

- Everything the daily run calls is keyless: `GetMostPlayedGames`, `appdetails`
  for names, `IUserReviewsService/GetAppReviews` for counts — one game and one
  language per call, ~4,250 calls and ~18 minutes per run.
- Only `get_all_apps()` (the catalog job) takes a key. It pages through
  `IStoreService/GetAppList` 50,000 apps at a time and upserts into
  `steam_apps`.

## Running and testing

From `analysis/`, with `SUPABASE_DB_URL` set:

```bash
.venv/Scripts/python.exe -m pytest           # all tests
TOP_N_GAMES=3 .venv/Scripts/python.exe run_daily.py   # cheap smoke run against live Steam + DB
```

CI does **not** run pytest (only `deploy-web.yml` runs tests, and only the C#
ones), so run it locally before pushing. Tests fake `SteamClient` and use an
in-memory writer; never call the real API from a test.

## Open items

- A run takes ~18 minutes of sequential keyless calls. The developer chose
  exact counts over speed; runtime may be revisited (concurrency within the
  keyless rate limit).
- The catalog refresh only upserts, so apps Steam drops stay searchable — not
  decided either way (ADR-011).
- Deferred architecture candidate: deepen the daily-job composition behind one
  seam (`run_daily_job`); the foreign-key write order in `run_daily.py`'s
  `main()` is untested.

## Decisions that apply here

ADR-001–004 (proxy, regions, concentration, Wilson), ADR-005 (shared database),
ADR-006 (test scope), ADR-009 (ranking eligibility), ADR-011 (catalog,
rotation, run pruning), RFC-001 (top-N scope).
