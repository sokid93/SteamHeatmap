# Steam Regional Popularity Heatmap

Which Steam games are disproportionately popular in each part of the world, inferred from the language of their reviews because Steam publishes no per-country data.

## Language

### Geography

**Language-as-proxy**:
The core data strategy: the distribution of a game's reviews across Steam review languages stands in for where its players are (ADR-001).
_Avoid_: country data, geo data

**Region**:
The country or group of countries one Steam review-language code stands for (ADR-002). A region's code is its review-language code.
_Avoid_: country, locale

**Blended region**:
A region spanning several countries because its language can't be split further (e.g. `english`); disclosed as such on the map.

### Scoring

**Share**:
The fraction of one game's reviews written in a region's language.

**Region baseline**:
The average share of a region's language across all tracked games in a run — what "normal" looks like for that region.
_Avoid_: average, mean share

**Wilson-adjusted share**:
The lower bound of the 95% Wilson interval of a share, so small samples can't produce extreme values (ADR-004).

**Concentration score**:
A game's Wilson-adjusted share divided by the region baseline: how many times more popular the game is in that region than a typical tracked game (ADR-003). Shown as ×values.
_Avoid_: popularity, intensity

**Ranking eligibility**:
A game is ranked in a region only with at least 50 reviews in that region's language; below that it still counts toward the region baseline (ADR-009).

### Games

**Top-N games**:
The current top ~100 games by live concurrent players, refreshed every day (RFC-001).

**Tracked game**:
A game scored in the daily run: a top-N game, or a searched game still inside its relevance window.

**Relevance window**:
How long a game stays tracked after it was last in the top-N or last searched.

**Featured game**:
The current global #1 by most-played rank; its heatmap is the map's landing state.

**Catalog**:
Every game Steam lists, by id and name — what search can reach, not what is scored.

**On-demand fetch**:
Scoring a game that isn't tracked, live, at the moment a visitor selects it from search (ADR-011).

### Runs

**Run**:
One complete daily scoring pass; the map always shows the latest run.

**Daily job**:
The scheduled process that produces a run.
