# Project Context: Steam Regional Popularity Heatmap

A web app showing, per country/region, which Steam games are most disproportionately popular there — using review-language distribution as a proxy for geography, since Steam has no public per-country data.

Read this file in full at the start of any session touching this project. Read individual ADRs in `adr/` only when working in the area they concern. Follow the development process in `docs/methodology.md` — strict TDD cycles, one commit per cycle, push per feature.

## Domain vocabulary

- **Region** — a country or group of countries inferred from a Steam review-language code. Most languages map to one country (e.g. `japanese` → Japan); some map to a blended group (e.g. `english` → US/UK/Canada/Australia/etc., merged and disclosed as such). See ADR-002.
- **Language-as-proxy** — the core data strategy: Steam review language distribution stands in for true per-country data, which Steam does not expose publicly. See ADR-001.
- **Concentration score** — how disproportionately popular a game is in a region, relative to that region's average share across all tracked games (not raw review volume). See ADR-003.
- **Wilson score (lower bound)** — the statistical adjustment applied to concentration scores so that small review samples don't produce misleadingly extreme rankings. Confidence level finalized at 95%. See ADR-004.
- **Ranking eligibility** — a game must have at least 50 reviews in a region's language to be ranked in that region; sub-threshold games still count toward the region's baseline. Protects against confident-but-tiny shares divided by tinier baselines, which Wilson cannot catch. See ADR-013.
- **Featured game** — the current global #1 by most-played rank; its heatmap is the map's landing state. The map always encodes one game at a time — see ADR-014.
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

As of 2026-07-21 — MVP fully working end to end, including the redesigned map:

- **Done** (issues #2–#11, #14 closed): walking skeleton; daily pipeline tracking the real top-100 most-played games across all 30 review languages (~3,100 keyless API calls/day, runs green on GitHub Actions, retries transient Steam 5xx/429 with backoff); full 30-region language mapping per ADR-002's concrete table; **ranking eligibility** — a game needs 50+ in-language reviews to rank in a region (ADR-013; the Arabic region drops to the grey no-data treatment as a result, so 29 regions currently display); Wilson confidence finalized at 95%; world map rendered from self-hosted Natural Earth GeoJSON, the D3 code living in `web/wwwroot/js/map.js` behind `initRegionMap(...)`; store links; always-visible disclosures; **production hosting** — live at https://steamheatmap.azurewebsites.net (Azure App Service F1 Linux, France Central, resource group `steamheatmap-rg`), deployed by `.github/workflows/deploy-web.yml` on pushes to `main` touching `web/`. The web app is template-free: no Bootstrap/jQuery, plain CSS only (ADR-010 fully realized).
- **Map redesign shipped** (ADR-014, grill-me completed 2026-07-18): the map always shows one game's concentration heatmap — landing on the featured game — replacing the region-level choropleth, whose intensity encoded language-community size rather than insight. Single-hue log ramp, fixed clamped domain [×⅛, ×8] (data-backed); fill semantics ramp/white/gray; blended regions signaled by synchronized member-country highlight + region-titled popups (resolves ADR-002's open mechanism); full dataset embedded in the page, no endpoints.
  - **#10** (per-game heatmap spine): pipeline persists most-played rank, view model exposes tracked games + per-game/per-region concentration lookup, map paints one game's ramp with headline and hover popup.
  - **#11** (selected-mode state machine): click enters selected mode (heatmap clears to white/gray, region gets a persistent highlight, side panel shows the region-titled top 10); clicking another region switches directly; hover-preview still works while selected; all three exit routes (re-click, click empty map space, Esc) restore heatmap mode.
  - **#14** (game search typeahead): client-side substring filter over the embedded, rank-ordered game list; empty input shows the rank-ordered top with the featured game first; selecting a suggestion repaints the heatmap/headline, exits selected mode if active, and clears the input; no-match hint discloses the top-100 dataset boundary.
- **Open**: nothing currently filed. Deferred polish noted on #11 (not filed as issues): blended regions hard to see as a unit pre-hover; friendlier visual form for ×values. The natural next design question — flagged in ADR-014 as a revisit trigger, not yet scoped — is **out-of-catalog search**: letting visitors search the full Steam catalog beyond the tracked top-100 would need a live endpoint, since the map currently has zero server round-trips after first paint. Architecture-review candidates deliberately deferred: deepen the daily-job composition (`run_daily_job` behind one seam), name-based column reads in `PostgresRankingRepository`.
- Pipeline needs no Steam API key — `GetMostPlayedGames` and `appreviews` are both public. Secrets: `SUPABASE_DB_URL` (GitHub Actions secret + local user env var + Azure app setting — update all three together when rotating, and prefer alphanumeric-only passwords: a special-char rotation once produced a pooler credential only the newest client libraries could authenticate against) and `AZURE_WEBAPP_PUBLISH_PROFILE` (GitHub Actions secret for the deploy workflow).
