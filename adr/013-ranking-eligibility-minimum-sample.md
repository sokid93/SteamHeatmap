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

## Amendment (2026-11-03): provisional — Steam no longer reports counts below 200

Steam retired `store.steampowered.com/appreviews` in late September 2026 (it
now redirects to the store homepage); the daily pipeline failed every day from
2026-09-25 and the map froze on run 87 (2026-09-24). The keyless replacement,
`IStoreBrowseService/GetItems` (ADR-012 amendment), changes the inputs this ADR
reasons about in two ways, measured against run 87's stored counts:

- **Counts are Steam's filtered review-score counts**, not `purchase_type=all`:
  104 of 157 games came back *lower* after 40 days of growth (median ×0.91),
  the biggest drops on key-reseller-heavy titles (Call of Duty ×0.55, Skyrim SE
  ×0.59), so key activations are most likely excluded. The same filter applies
  to both numerator and denominator, so shares barely move (median |Δshare|
  0.0003); a small regional tilt remains (Hungarian −2.6%, Japanese +6%).
- **A language's count is omitted below 200 reviews.** 757 of run 87's 3,916
  ranked rows (all ≥50) had 50–199 reviews and would now have no count; small
  languages lose half their ranked games or more (Indonesian 68%, Greek 59%).

Decision, provisional until a source with exact sub-200 counts is found:

- The 50-review threshold stays as written, but in practice nothing between
  50 and 199 can be ranked: an unreported count is not ranked.
- **An unreported count enters the baseline as a zero share**, in the spirit
  of this ADR's "near-zero shares stay in the baseline". Measured on run 87:
  zero-imputation lands baselines a median 14% low, excluding the unknown games
  a median 14% high, but in small languages exclusion is far worse (Indonesian
  +220% vs −60%, Bulgarian +167% vs −33%).
- The web's on-demand path reads an unreported count as 0 inside its Steam
  adapter: it computes no baseline, so the distinction has no effect there.

Recomputing run 87's concentrations from GetItems' counts shifts them a median
2–14% per language, and top-10 rankings overlap 8–10/10 in most languages
(French 6/10). The comparison is confounded with 40 days of real drift, since
the old endpoint cannot be queried any more.
