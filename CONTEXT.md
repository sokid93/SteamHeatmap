# Project Context: Steam Regional Popularity Heatmap

A web app showing, per country/region, which Steam games are most disproportionately popular there — using review-language distribution as a proxy for geography, since Steam has no public per-country data.

Read this file in full at the start of any session touching this project. Read individual ADRs in `adr/` only when working in the area they concern. Follow the development process in `docs/methodology.md` — strict TDD cycles, one commit per cycle, push per feature.

## Domain vocabulary

- **Region** — a country or group of countries inferred from a Steam review-language code. Most languages map to one country (e.g. `japanese` → Japan); some map to a blended group (e.g. `english` → US/UK/Canada/Australia/etc., merged and disclosed as such). See ADR-002.
- **Language-as-proxy** — the core data strategy: Steam review language distribution stands in for true per-country data, which Steam does not expose publicly. See ADR-001.
- **Concentration score** — how disproportionately popular a game is in a region, relative to that region's average share across all tracked games (not raw review volume). See ADR-003.
- **Wilson score (lower bound)** — the statistical adjustment applied to concentration scores so that small review samples don't produce misleadingly extreme rankings. Confidence level finalized at 95%. See ADR-004.
- **Ranking eligibility** — a game must have at least 50 reviews in a region's language to be ranked in that region; sub-threshold games still count toward the region's baseline. Protects against confident-but-tiny shares divided by tinier baselines, which Wilson cannot catch. See ADR-013.
- **Top-N games** — the fixed seed set (current top ~100 games by live Steam concurrent-player count) that the daily pipeline tracks. Not the full Steam catalog. See ADR-005.
- **Daily job** — the single unified batch process (Python) that fetches top-N rankings and per-language review counts once per day, computes scores, and writes results to Postgres.

## Architecture at a glance

- **Web app**: C# / ASP.NET Core MVC, single project with folder-based (not project-based) separation between domain / infrastructure / web layers. Razor views + plain CSS + D3.js for the map visualization only.
- **Batch/analysis job**: Python, runs daily via GitHub Actions (scheduled workflow), independent of wherever the web app is hosted.
- **Integration between C# and Python**: shared Postgres database only (Supabase, free tier). No direct process-to-process coupling — see ADR-006.
- **Data source**: Steam public Web API. `ISteamChartsService`/`GetMostPlayedGames` for rankings; `appreviews` (with `num_per_page=0`, once per language code) for language breakdown. ~29 calls/game/day, well under the 100k/day API cap.
- **Hosting**: Azure App Service (F1, free tier) for the web app; Supabase for Postgres; GitHub Actions for both scheduling and CI. VPS migration planned later, deliberately deferred (see ADR-007).
- **Testing**: TDD on domain-level logic only (Wilson scoring, region mapping, aggregation). Integration/e2e tests deferred until needed. `ISteamClient` (C#) / `SteamClient` protocol (Python) is the seam faked in tests — see the `tdd` skill's `mocking.md`.
- **Repo**: single monorepo, `/web` (C#) and `/analysis` (Python) side by side, single shared documentation.

## Current status

As of 2026-07-14 — MVP largely working end to end:

- **Done** (issues #2–#8 closed): walking skeleton; daily pipeline tracking the real top-100 most-played games across all 30 review languages (~3,100 keyless API calls/day, runs green on GitHub Actions, retries transient Steam 5xx/429 with backoff); full 30-region language mapping per ADR-002's concrete table; world map rendered from self-hosted Natural Earth GeoJSON with hover/click region panels; store links; always-visible disclosures; **production hosting** — live at https://steamheatmap.azurewebsites.net (Azure App Service F1 Linux, France Central, resource group `steamheatmap-rg`), deployed by `.github/workflows/deploy-web.yml` on pushes to `main` touching `web/`.
- **Open**: #9 scoring/tuning against real data (needs a grill-me — note the color-scale saturation evidence in its comments); #10 blended-region visual treatment (needs a grill-me); #11 map interaction — click to pin a region, hover top-3 popup.
- Pipeline needs no Steam API key — `GetMostPlayedGames` and `appreviews` are both public. Secrets: `SUPABASE_DB_URL` (GitHub Actions secret + local user env var + Azure app setting — update all three together when rotating, and prefer alphanumeric-only passwords: a special-char rotation once produced a pooler credential only the newest client libraries could authenticate against) and `AZURE_WEBAPP_PUBLISH_PROFILE` (GitHub Actions secret for the deploy workflow).
