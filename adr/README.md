# Architecture decision records

An ADR records a decision that shapes the system and is expensive to reverse:
the data strategy, the scoring model, the stack, how the two codebases
integrate, how the map encodes data. Changing one means rewriting code across
the project, so ADRs are amended (with a dated section) rather than quietly
edited.

Pragmatic, provisional choices — ones made to keep the product moving and
expected to be revisited — live in [`rfc/`](../rfc/) instead. Reference notes
on external APIs live in [`docs/`](../docs/).

| ADR | Decision |
|---|---|
| [ADR-001](001-language-as-proxy-for-region.md) | Review language as a proxy for region |
| [ADR-002](002-language-to-region-mapping.md) | Language-to-region mapping, including blended regions |
| [ADR-003](003-concentration-score-over-raw-volume.md) | Rank by relative concentration, not raw volume |
| [ADR-004](004-wilson-score-for-ranking.md) | Wilson lower bound to rank concentration |
| [ADR-005](005-csharp-python-shared-database-integration.md) | C# and Python integrate only through a shared Postgres database |
| [ADR-006](006-tdd-scope-and-seams.md) | TDD scope and test seams; single C# project |
| [ADR-007](007-primary-stack-csharp-dotnet.md) | C# / ASP.NET Core MVC as the primary web stack |
| [ADR-008](008-monorepo-structure.md) | Single monorepo |
| [ADR-009](009-ranking-eligibility-minimum-sample.md) | 50 in-language reviews to be ranked; Wilson at 95% |
| [ADR-010](010-per-game-heatmap-encoding.md) | The map encodes one game at a time |
| [ADR-011](011-out-of-catalog-search.md) | Out-of-catalog search |

## Renumbering (2026-11-18)

Until 2026-11-18 all sixteen records were ADRs, numbered 001–016. Commits,
issues and pull requests from before that date use the old numbers:

| Old | New | | Old | New |
|---|---|---|---|---|
| ADR-001–004 | unchanged | | ADR-011 | ADR-008 |
| ADR-005 | RFC-001 | | ADR-012 | [docs/steam-web-api.md](../docs/steam-web-api.md) |
| ADR-006 | ADR-005 | | ADR-013 | ADR-009 |
| ADR-007 | RFC-002 | | ADR-014 | ADR-010 |
| ADR-008 | ADR-006 | | ADR-015 | RFC-004 |
| ADR-009 | ADR-007 | | ADR-016 | ADR-011 |
| ADR-010 | RFC-003 | | | |
