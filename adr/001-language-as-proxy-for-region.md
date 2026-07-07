# ADR-001: Use review-language distribution as a proxy for country/region

## Context
The product goal is a heatmap of "most played games by country." Steam's public Web API does not expose per-country player or review data — that data (if it exists at all) lives only in Valve's non-public partner backend. Third-party sources (GameDiscoverCo newsletter analyses, Kaggle datasets) offer true country-level splits, but are static snapshots, not live/automatable, and don't cover the full dynamic top-N list.

## Decision
Use Steam's public per-language review counts (`appreviews` endpoint, filtered by language code) as a proxy for region. Accept lower geographic fidelity in exchange for a live, fully automatable, public-API-only pipeline.

## Alternatives rejected
- Static third-party datasets: not live, not automatable, coverage doesn't match our dynamic top-N scope.
- Scraping Steam's regional store front-end pages: fragile, likely against Steam's terms — ruled out.

## Consequences
- Some languages map cleanly to one country (Japanese → Japan); others must be treated as blended regions (English → US/UK/Canada/Australia/etc.). See ADR-002.
- The product must visibly disclose that it uses language as a proxy, not official country data (agreed UI requirement, not yet implemented).
