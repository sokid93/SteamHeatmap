# ADR-012: Steam Web API usage mechanics and terms-of-use compliance

## Context
Needed to confirm the daily pipeline's API usage is technically sound and compliant with Valve's Steam Web API Terms of Use before committing to the design.

## Findings (verified, not assumed)
- Steam Web API Terms of Use: free to use, capped at 100,000 calls/day per key; must not imply Valve endorsement/affiliation with the app; key must be kept confidential and out of source control.
- Per-game daily fetch: 1 call (`appreviews`, `language=all`, `num_per_page=0`) for the total review count, plus 1 call per language code (also `num_per_page=0`) to get that language's `total_reviews` from `query_summary` — no pagination needed since we only need counts, not review text. ~29 calls/game/day.
- At ~100 tracked games, that's ~2,900 calls/day — well under the 100k/day cap. No throttling infrastructure required for MVP scale.

## Decision
- Store the Steam Web API key only as a GitHub Actions secret (never committed to the repo), consistent with the existing CI/CD and secrets approach.
- Include a visible "data powered by Steam, not affiliated with Valve" disclosure in the UI (same convention as SteamCharts), satisfying the non-affiliation clause of the terms of use.

## Consequences
- No rate-limiting/backoff logic is required for MVP scale, though it would be a reasonable addition if the tracked game count grows substantially later.

## Amendment (2026-08-14): one keyed exception — the catalog job
Discovered while building issue #24 (weekly Steam catalog cache, ADR-016): `ISteamApps/GetAppList/v2`, the endpoint the daily pipeline had (correctly, per the 2026-07-10 finding) assumed stayed keyless for everything, no longer exists on Steam's live API. Its replacement, `IStoreService/GetAppList/v1`, requires the `key=` param this ADR's original decision already anticipated storing.

- **Scope**: only `RequestsSteamClient.get_all_apps()`, called solely from `refresh_catalog.py` (the weekly catalog job), takes an `api_key`. `GetMostPlayedGames` and `appreviews` — everything the daily pipeline and the live web app use — remain public and keyless, unchanged.
- **Mechanics confirmed live 2026-08-14**: `IStoreService/GetAppList` is paginated (up to 50,000 apps/page via `max_results`, cursor via `last_appid`/`have_more_results`), unlike the old single-shot response. Response shape is `{"response": {"apps": [{"appid", "name", ...}], "have_more_results", "last_appid"}}`, not the old `{"applist": {"apps": [...]}}`. Default filters return games only (no DLC/software/videos/hardware) — a behavior change from the old endpoint's unfiltered dump, and a better fit for #24/#26's game-search use case, not just an incidental side effect.
- **Storage**: `STEAM_API_KEY` stored as a GitHub Actions secret (consistent with this ADR's original decision) and as a local user env var for manual runs; passed only to `weekly-catalog-refresh.yml`'s job env, never to the daily pipeline workflow.
