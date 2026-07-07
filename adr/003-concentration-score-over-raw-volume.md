# ADR-003: Rank games per region by relative concentration, not raw review volume

## Context
With only ~100 tracked games, ranking each region's "top 3" by raw review count per language would almost always surface the same handful of global blockbusters in every region — an uninteresting, low-insight result for a heatmap product.

## Decision
Rank games per region by **relative concentration**: how much a region's share of a specific game's reviews exceeds that region's average/baseline share across all tracked games. This surfaces games disproportionately popular in a specific region even when their absolute numbers are smaller than a global blockbuster's.

## Alternatives rejected
- Raw review volume per region: simpler, but produces repetitive, low-insight "top 3" lists dominated by the same mega-hits everywhere.

## Consequences
- Requires computing a per-language baseline (average share across all tracked games) as part of the daily pipeline, not just per-game numbers in isolation.
- Introduces a small-sample noise problem, addressed in ADR-004.
