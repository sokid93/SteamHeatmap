---
paths:
  - "analysis/steamheatmap/scoring.py"
  - "analysis/steamheatmap/pipeline.py"
  - "analysis/tests/test_scoring.py"
  - "web/Domain/OnDemandScoring.cs"
  - "web/Domain/OnDemandGameFetcher.cs"
  - "web/tests/OnDemandScoringTests.cs"
---

# Scoring parity between Python and C#

A game scored on demand by the web app must land on exactly the number the
daily pipeline would give it, or it is painted a different color for the same
inputs. The two runtimes share no library (ADR-005), so the logic is ported and
must be changed on both sides together:

| Python | C# |
|---|---|
| `scoring.py` `wilson_lower_bound`, `_Z_95` | `OnDemandScoring.WilsonLowerBound`, `Z95` |
| `scoring.py` `concentration_score` | `OnDemandScoring.ConcentrationScore` |
| `pipeline.py` `MIN_REVIEWS_TO_RANK` | `OnDemandGameFetcher.MinReviewsToRank` |
| zero-review games excluded | zero total reviews → "not enough reviews" |

`region_baseline_share` is deliberately not ported: the web reads the baselines
the daily run persisted in `region_baselines`.

The C# tests reuse `test_scoring.py`'s exact expected values. When a formula
changes, change the Python test's expected value, then copy the same value into
the C# test — never re-derive it independently on either side.
