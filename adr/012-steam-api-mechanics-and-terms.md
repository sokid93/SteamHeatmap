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
