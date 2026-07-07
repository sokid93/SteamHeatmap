# ADR-005: MVP tracks a fixed top-N "currently most played" list, not the full catalog

## Context
Steam has 100k+ listed apps. Pulling per-language review data for the entire catalog daily is neither realistic nor necessary for the product goal.

## Decision
MVP tracks roughly the top 100 games by live Steam concurrent-player count (`GetMostPlayedGames`/`ISteamChartsService`, a genuine public, cheap, single-call endpoint). The pipeline's per-game fetch/cache logic is designed as a reusable unit so it can later support on-demand fetch for arbitrary user-searched games (future feature, not MVP) without rearchitecting.

## Alternatives rejected
- Ranking by total review count instead of current players: biased toward legacy titles, less "what's trending now."
- User-curated seed list: cheaper but less "explore any game."
- Full catalog: not feasible at reasonable cost/complexity.

## Consequences
- The search-box feature (user picks any game, not just top-100) is explicitly out of scope for MVP but the fetch/cache unit must be written generically enough to support it later without a rewrite.
