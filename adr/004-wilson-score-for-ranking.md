# ADR-004: Use Wilson score interval (lower bound) to rank concentration, not raw percentage

## Context
Raw concentration percentage (ADR-003) is unreliable at low sample sizes — e.g. a game with only 12 total reviews, 8 of them in one language, would show a mathematically extreme 67% concentration that is statistically meaningless. This risk concentrates in two cases: newly-viral games that enter the top-N with few total reviews, and minority-language buckets even for otherwise well-reviewed games. Linear regression was considered and rejected as a category mismatch — this is a proportion-with-uncertainty problem, not a predictor/outcome relationship.

## Decision
Rank by the Wilson score interval lower bound of the concentration percentage, not the raw percentage. This is the same class of technique used for ranking-by-proportion-with-varying-sample-size problems generally (e.g. comment ranking systems). A concentration score from a small sample is pulled down (wide uncertainty); the same score from a large sample stays close to its raw value.

## Alternatives rejected
- Fixed minimum-review threshold (simple cutoff): simpler, but a blunt binary in/out rule rather than a continuous, statistically principled adjustment.
- Bayesian/Laplace shrinkage toward baseline: a legitimate alternative, not chosen — Wilson score preferred for statistical precision.
- Linear regression: mismatched tool for a proportion-confidence problem; ruled out.

## Consequences
- This is core, testable domain logic — belongs in the unit-tested domain layer (see `tdd` skill), not a UI-side filter.
- Exact behavior (e.g. confidence level used, minimum viable sample where results are excluded entirely rather than just down-ranked) is an implementation detail to pin down with real data during development, not decided in the abstract.
