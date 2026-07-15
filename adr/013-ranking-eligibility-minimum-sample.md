# ADR-013: Games need 50 in-language reviews to be ranked in a region; Wilson stays at 95%

## Context

The first full runs produced absurd top rankings in low-review-volume regions:
run 12's Arabic #1 was "Where Winds Meet" at ×16.09 concentration backed by
**9 Arabic reviews** (out of 111,974 total); the Arabic top-10 included entries
backed by 1 and 2 reviews. The Wilson lower bound (ADR-004) cannot fix this
case: with a huge total-review sample, a tiny share is *statistically
confident* — the explosion comes from dividing it by an even tinier regional
baseline, not from sample unreliability. Meanwhile the case Wilson is designed
for (FiveM's 42/335 Turkish reviews) it already handles by shrinking the share
before ranking.

Evidence from run 12 (2026-07-15), games eligible per region at candidate
thresholds: every region except Arabic keeps 57+ of the ~100 tracked games at
N=50; Arabic has one game at N=10 and zero at N≥25 — Arab-world Steam users
overwhelmingly review in English (the region's median concentration is 0.000).

## Decision

- A game must have **at least 50 reviews in a region's language** to be ranked
  in that region ("ranking eligibility"). The pipeline simply does not emit
  sub-threshold game×region rows.
- Sub-threshold games **still count toward the region baseline** — "almost
  nobody reviews in Arabic" is the region's true normal; excluding near-zero
  shares would inflate the baseline and silently deflate every score.
- The Arabic region consequently drops off the map entirely, rendering as the
  existing grey "no data" treatment. Showing nothing is more honest than
  shading a region group on 9 reviewers' evidence.
- The Wilson confidence level is **finalized at 95%** (z ≈ 1.96), closing
  ADR-004's placeholder. Its one remaining job — shrinking mid-size samples —
  is demonstrably done well, and changing two variables at once would have
  muddied the review of what the threshold fixed.

## Alternatives rejected

- **Raising the Wilson confidence level (99%)**: does not touch the offenders —
  their shares are backed by 100k+ totals and barely shrink at any z.
- **Minimum total-review threshold per game**: the outliers have huge totals so
  it misses them, while evicting small-catalog games (FiveM, 335 reviews) whose
  regional signal is plausibly genuine and already Wilson-shrunk.
- **Enforcing the threshold on the C# read side** (SQL filter or view-model
  rule): puts a scoring-domain rule on the display side of the seam, in a
  different language from the score it gates.
- **Writing all rows plus an `eligible` flag**: keeps sub-threshold rows
  queryable for retuning, but costs a schema change for rows the app never
  shows — and each daily run regenerates everything anyway.

## Consequences

- The map's top concentrations remain large (×11–12 for Japan, Indonesia,
  Vietnam — real cultural hits backed by hundreds+ of reviews); the color-scale
  saturation problem is therefore *not* solved by this decision and stays with
  issue #10.
- The threshold is a named constant in the pipeline, revisitable with evidence;
  post-threshold rankings now cleanly show whether Wilson needs retuning.
