# Working methodology

This project is built by a human–AI pair: the human owns product decisions,
reviews everything, and steers the process; the AI agent (Claude Code) does the
implementation work in a disciplined TDD loop. This document describes the
process itself and — just as importantly — how the process has been *refined
over time* by reviewing each day's output and feeding corrections back into the
next iteration.

## The development loop

Every feature follows the same cycle:

1. **Red** — write one test that asserts **one behavior**, run it, see it fail.
   Multiple asserts are acceptable only when they describe a single behavior
   (e.g. the fields of one returned record). If a test wants to check two
   things, it becomes two tests — smaller steps, smaller commits.
2. **Green** — write the *minimum* code that makes the test pass, even when the
   minimal version is naive. The next test forces the generalization.
3. **Refactor** — only when there is duplication or a name worth improving,
   with tests staying green.
4. **Commit** — one conventional commit (`feat:`/`test:`/`fix:`/`refactor:`/
   `chore:`, scoped like `feat(analysis):`) per cycle, never batching several
   cycles together. **Push happens once per completed feature**, so CI and the
   remote stay quiet while the local history keeps every step.

The result is a git history you can read like a narrative. Example — issue #4
(full language-to-region mapping) landed as seven consecutive commits, each one
a visible cycle:

```
9c32ff1 feat(analysis): map the 19 single-country review languages
4ac40c1 feat(analysis): map the 11 blended regions with ISO alpha-2 members
9a28c5d feat(analysis): expose the full supported language code list
6e638da test(analysis): guard the one-region-per-country invariant
400ecde feat(analysis): daily job scores all 30 review languages
8406aec refactor(web): drop the UK-to-GB shim now region data is strict ISO
c2277da test(analysis): pin one region row set per scored language
```

A production bug found during a live run follows the same pattern — red test
reproducing the failure first, then the fix (`6ea4c39 fix(analysis): exclude
zero-review games from scoring and baseline`), then a second test pinning the
companion behavior (`30e9fb8`).

## What gets tested (and what deliberately doesn't)

Per [ADR-008](../adr/008-tdd-scope-and-seams.md): TDD applies to domain logic
worth testing — pure scoring math, region mapping, pipeline orchestration
(against a fake `SteamClient` and in-memory writer), and C# view-model shaping
(against a fake `IRankingRepository`). Framework glue — controllers, EF/Npgsql
wiring, Razor views, the real HTTP client — stays untested by design until an
integration-test need actually arises.

Test expectations come from independently worked-out values (hand calculations,
known Wilson-score references), never from re-running the formula under test.

## Verification before closing

Unit tests passing is necessary but not sufficient. Before an issue closes, the
change is exercised end-to-end: the real pipeline runs against the live Steam
API and Postgres, and the web app is driven in a headless browser (screenshots,
scripted hover/click assertions) against real data. Two production bugs so far
were caught exactly this way — a `postgresql://` URI Npgsql couldn't parse, and
a top-100 game with zero reviews crashing the scoring — both invisible to unit
tests, both found before closing the issue that introduced them.

## Readability first

When a shorter or faster implementation makes code harder to read, the readable
version wins: clear names, explicit intermediate variables, straightforward
control flow over dense one-liners. Optimisation for speed or line count only
happens against a demonstrated need (a measured bottleneck or an explicit
decision). Discovered optimisation opportunities are surfaced in review or in
issues, not applied silently.

## The human–AI feedback loop

The collaboration is structured to keep the feedback loop short and to make
each iteration start where the last one left off:

- **Decisions are interviewed, not assumed.** Anything genuinely open (region
  groupings, scoring tunings, visual treatments) is resolved in a structured
  interview ("grill-me") where the agent presents options with a recommendation
  and the human decides. Outcomes land in ADRs, so decisions are permanent and
  attributable. Issues explicitly flag which decisions require this.
- **The agent works autonomously between decision points**, in the TDD loop
  above, closing issues with an evidence trail (commit list, verification
  results) written into the issue itself.
- **The human reviews the artifacts** — commit history, tests, the running
  app — and gives corrective feedback on the *process*, not just the code.
- **Feedback becomes a persistent rule immediately.** Corrections are written
  to the agent's cross-session memory the moment they're given, so the next
  session starts already improved instead of repeating the mistake. Evidence
  the data surfaces (e.g. real concentration ranges saturating the color
  scale) is parked on the issue that owns the decision rather than acted on
  unilaterally.

### How the workflow has evolved (chronological)

This log is the point: the process itself is iterated on, deliberately, with
each refinement dated and traceable to the review that triggered it.

| Date | Refinement | Trigger |
|---|---|---|
| 2026-07-07 | ADRs + PRD via grill-me interviews before any code; issues as vertical slices | Project kickoff — decisions documented before implementation |
| 2026-07-08 | Conventional commits; commit after every TDD cycle instead of batching a feature into one commit | Review of the walking-skeleton session's history |
| 2026-07-08 | Open design decisions flagged in issues for future grill-me sessions instead of being decided silently | Walking-skeleton scoping — deferred blended-region and tuning decisions |
| 2026-07-10 | Strict cycle granularity: one behavior per test, minimum code to green, commit each cycle — reviewer must be able to *see the process*, not just the result | Review of `d4514ed` (Wilson scoring): working code and tests, but the steps were invisible |
| 2026-07-10 | Push once per feature (commits stay per-cycle) | Balancing granular history against remote/CI noise |
| 2026-07-10 | Readability over cleverness as an explicit standing rule | Same review session |
| 2026-07-10 | Stage files explicitly, never `git add <dir>` | A directory-wide `add` swept an unverified file into a test-only commit; caught and split before push |
| 2026-07-10 | End-to-end verification with a headless browser (scripted hover/click) added to the definition of done for UI work | Map interaction couldn't be honestly verified by unit tests or static screenshots |
| 2026-07-10 | Real-data findings that belong to an open decision get parked on the owning issue with evidence, not fixed inline | First full 30-language run saturated the map's color scale — evidence filed on #9, which owns scoring/tuning |
| 2026-07-10 | Every session ends with a documentation pass: refresh CONTEXT.md status, append any new row to this table, adjust the README if the product changed | This documentation set was written days after the code it describes — catching up is costlier than keeping up |
| 2026-07-14 | Secrets propagate by reference (read from the local env var into each target), never through chat, logs, or command echoes | Supabase password rotation — the previous password had passed through chat, which is what forced the rotation |
| 2026-07-14 | CI-side experiments run from a throwaway branch via `gh workflow run --ref <branch>`, never by pushing debug code to `main` | Rotated DB password failed only from GitHub Actions; needed runner-side evidence (secret hash, driver matrix) without touching the production workflow |
| 2026-07-14 | Debug by eliminating hypotheses with byte-level evidence before blaming any component | Same incident: encoding, shell arg-mangling, and secret transport were each disproved by hash comparison inside the runner — the real culprit was a Supabase-side credential bug fixed by re-rotating |

The table grows as the process does; an entry that never gets superseded is as
informative as one that does.
