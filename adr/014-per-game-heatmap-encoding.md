# ADR-014: The map encodes one game at a time

## Context
The original map colored every region by its **top game's** concentration on a linear [0, 2] domain. Run-12 evidence (filed on #10) showed the surviving regional tops span ×1.70–×12.16, saturating 29 of 30 regions at full red. The paused grill-me's standing fix was log normalization — but the 2026-07-18 session surfaced a deeper problem: comparing concentration **across regions** is structurally confounded by language-community size. English is roughly a third of all Steam reviews, so no game can be many-times over-represented against that baseline, while tiny communities (Indonesian) reach ×12 easily. The default choropleth therefore mostly painted "smaller language community = redder" — an artifact, not insight. Normalization would have fixed the saturation and kept the confound.

Concentration (ADR-003) was designed to answer "where is *this game* disproportionately popular?" — one game, all regions, same units. That is the comparison the color should encode.

## Decision
The map always shows **one game's** concentration heatmap:

- **Landing state**: the heatmap of the featured game — the current global #1 by most-played rank, which the pipeline now persists. A headline above the map names it ("Where is *X* popular?").
- **Color scale**: single-hue sequential ramp, log-transformed, **fixed domain clamped to [×⅛, ×8]**. Data-backed: the latest run's 2,562 eligible scores have p02 ≈ ×0.12 and p98 ≈ ×3.77 (max ×12.12), so the bounds clamp ~2% at each end. Fixed (not per-game dynamic) so a flat game honestly looks flat and colors mean the same thing across searches. Real ×values shown on hover are the corrective for clamped outliers. No map legend: "darker = more popular here" is the entire encoding.
- **Fill semantics** (each fill means exactly one thing in every mode): **ramp** = eligible score for the shown game; **white** = region tracked but nothing to show (game below ADR-013's 50-review threshold in heatmap mode; unselected region in selected mode); **gray** = region outside the dataset entirely.
- **Blended-region mechanism** (resolves ADR-002's open question): interaction-driven — hovering any member country border-highlights **all** member countries simultaneously; popups and panels are titled by region ("English-speaking regions"), with the member list in a blended note. No permanent static mark (hatching rejected as un-keyed extra ink).
- **Data delivery**: the full latest-run dataset (~100 games × 30 regions, ~25 KB gzipped) is embedded in the server-rendered page; no JSON endpoints. Client-side interactions never touch the server after first paint — which neutralizes Azure F1 cold starts. Revisit trigger: dataset growth toward ~50× (full-catalog tracking) or the out-of-catalog search feature, which inherently needs an endpoint and would make embedding the fast path, not the casualty.

## Alternatives rejected
- **Region-level choropleth with log/quantile normalization**: fixes saturation, keeps the community-size confound.
- **Diverging two-hue palette centered at ×1**: semantically attractive (over/under-representation) but demands a legend; the over/under story lives in the hover numbers instead.
- **Dynamic per-game color domain**: maximizes contrast but stretches a flat ×0.9–×1.1 game across the full ramp — an exaggeration of reality.
- **Rendering ineligible regions at the ramp's light end**: ineligibility means *unknown*, not unpopular; painting it as data would undo ADR-013's honesty.
- **Per-game JSON endpoint**: solves a payload problem we don't have, at the cost of F1 cold-start latency on every search.

## Consequences
- The pipeline persists each game's most-played rank (drives the featured game and search-suggestion ordering).
- The view model owns every decision (featured game, per-game scores, eligibility, top-10 per region, rank-ordered game list) under fake-repository TDD; `map.js` only paints and transitions state (ADR-008 split).
- Scores beyond ×8 render identically; the hover popup always carries the real number.
- The map's region-level "at a glance" comparison is gone by design; region insight moves to hover (top 3) and selected mode (top 10).
