# ADR-016: Out-of-catalog search — cached catalog typeahead, on-demand live fetch, and a relevance-based tracked-game rotation

## Context
#14 shipped client-side substring search over the embedded top-100 dataset only. ADR-005 explicitly deferred full-catalog search ("user picks any game, not just top-100") but required the pipeline's per-game fetch/cache logic to stay generic enough to support it later — it does (`run_pipeline(steam, writer, app_ids, language_codes)` already takes arbitrary app_ids). ADR-014 embedded the full latest-run dataset in the page specifically to keep zero server round-trips after first paint, and named "the out-of-catalog search feature" as the trigger that would force a live endpoint.

This grill-me (2026-08-08) works out that shape end-to-end, under two framing constraints from the developer: don't design around Steam's 100k-call/day cap (~2,900/day used today) since it isn't a problem yet, but do optimize database usage and data freshness so that repeat searches don't always cold-fetch, and the daily top-100 refresh isn't the only thing kept warm.

## Decision

1. **Catalog typeahead source**: a new `steam_apps (app_id, name)` table, refreshed weekly (Sundays) by a new GitHub Actions workflow (`weekly-catalog-refresh.yml`) calling Steam's `ISteamApps/GetAppList` once and upserting. Kept independent of the daily pipeline — it's cheap, changes rarely, and a bad catalog refresh shouldn't block the daily scoring run or vice versa.

2. **Search stays two-tier, preserving ADR-014's zero-round-trip fast path**: the existing instant client-side filter over the embedded dataset (top-100 ∪ still-relevant searched games, see #4) remains the first thing shown while typing. A debounced server call to a new catalog-search endpoint (querying `steam_apps`) fires only when the local match set is thin. A result that's already tracked — found via either path — renders instantly client-side; the network is only paid for genuinely untracked games.

3. **Selecting an untracked game triggers a live, on-demand fetch-and-score**, not a "come back tomorrow" queue. C# gains its own minimal, request-scoped Steam-calling path (calls parallelized — ~29 concurrent, not sequential like the batch job — to keep click-to-paint latency low), which fetches total + per-language review counts, scores concentration against the *current* run's region baselines, and writes through the same schema Python writes, under the same latest `run_id` — so the result is immediately visible to every other visitor, not just the requester.
   - Region baselines were previously never persisted (`region_baseline_share` lived only in-memory during a Python run, and includes sub-eligibility-threshold games' shares that never get written to `region_scores`). A new `region_baselines (run_id, region_code, baseline_share)` table now persists them so the on-demand path can score a new game consistently with everyone else's colors, without recomputing from scratch.
   - A game with zero total reviews, or that produces zero region-eligible rows, shows an explicit "not enough reviews yet" message instead of a silently blank map, and is **not** persisted into ongoing tracking — a permanently-empty entry isn't worth a daily refetch.
   - The UI shows a loading state during the fetch and an honest failure message on error/timeout — never a silent fallback to stale data.
   - This narrows ADR-006's "Python is the only Steam caller" framing: Python remains the sole *batch* scorer; C# gains a narrow, request-scoped Steam-calling path solely for on-demand search.

4. **The daily job's app_id list becomes `today's real top-100 ∪ still-relevant searched games`**, deduped. A single `last_relevant_at` timestamp on `games` is bumped by either signal — appearing in today's actual top-100 fetch, or a user selecting/searching an already-tracked game — collapsing what would otherwise be two eviction rules into one: "is `last_relevant_at` within the freshness window." A game that drops out of today's top-100 isn't evicted immediately; it just stops being bumped by that path and decays through the same window as any searched game, so games hovering near rank 100 don't cause repeated add/remove/refetch churn, and a comeback within the window needs no cold re-fetch.
   - `most_played_rank` is explicitly cleared to `NULL` for any tracked game not in today's real top-100 fetch. Previously it was only ever upserted, never cleared — harmless while top-100 was the only source of tracked games, but would otherwise let a stale rank misrepresent a searched-only game as currently charting, including corrupting the featured-game pick (which orders by rank).

5. **Run-history retention**: the daily job prunes `runs`/`region_scores`/`region_baselines` to the 3 most recent runs after each successful write, by run count rather than calendar time (manual `workflow_dispatch` reruns can land same-day). Nothing has ever read anything but the latest run; this bounds storage growth that this feature otherwise ties directly to search activity.

## Alternatives rejected
- **Live Steam search-suggest endpoint per keystroke** instead of a cached local catalog: couples every keystroke to Steam's latency and an undocumented endpoint.
- **Always-server-side search**, dropping the embedded fast path: makes the common case (searching an already-tracked game) pay a round trip it doesn't need.
- **Queuing untracked searches for the next daily run** instead of live fetch: simpler and zero new architecture, but defeats the "search any game" immediacy that's the point of the feature.
- **Keeping on-demand results out of the shared run** (request-scoped only): avoids a live run's dataset changing mid-day, but means two users searching the same new game an hour apart don't share the payoff same-day.
- **Fixed-size LRU cap on the searched-game set**: bounds worst-case daily runtime precisely but needs an arbitrary ceiling picked up front; a relevance-window decay (`last_relevant_at`) is need-based instead.
- **Folding the weekly catalog refresh into the daily job**: one fewer workflow file, but couples a rarely-changing, cheap catalog list to the daily scoring run's failure/success for no benefit.

## Consequences
- Narrows ADR-006's "Python is the only Steam caller" framing — that ADR is worth a pointer note to this one so a future reader doesn't treat it as still-absolute.
- Closes ADR-005's deferred "search-box feature... explicitly out of scope for MVP."
- Revisits, but doesn't reverse, ADR-014's zero-round-trip decision: the top-100 embed stays, augmented by still-relevant searched games; a live endpoint now exists, but only pays for the genuinely-new-search case — exactly the trigger ADR-014 named for revisiting it.
- `games.most_played_rank` semantics change: `NULL` now means "not currently top-100" (the game may still be tracked via `last_relevant_at`), not "never was top-100."
- New schema: `steam_apps`, `region_baselines`, `games.last_relevant_at`. New GitHub Actions workflow: `weekly-catalog-refresh.yml`. New C#-side Steam-calling code (previously Python-only).
