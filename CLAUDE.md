# SteamHeatmap

A world map of which Steam games are disproportionately popular in each region,
using review language as a proxy for geography. Live at
https://steamheatmap.azurewebsites.net. The repo doubles as a portfolio piece:
code, history and docs are meant to be read.

@CONTEXT.md

## Where context lives

| File | Covers | Loads |
|---|---|---|
| `CLAUDE.md` (this file) | Project-wide rules, architecture, secrets | Every session |
| `CONTEXT.md` | Domain glossary — use its terms in code, tests, issues | Every session (imported above) |
| `CLAUDE.local.md` | This machine's paths and tools; not committed | Every session |
| `analysis/CLAUDE.md` | Python daily job, catalog job, Steam client, schema | When a file under `analysis/` is touched |
| `web/CLAUDE.md` | C# web app, map, on-demand path, styling, deploy | When a file under `web/` is touched |
| `.claude/rules/*.md` | Invariants shared across the C#/Python boundary | When a matching file is touched |
| `adr/`, `rfc/`, `docs/steam-web-api.md` | Decisions and API reference | Read when working in their area |
| `docs/methodology.md`, `docs/history.md` | Process evolution, what shipped | Read when needed |

**Grill-me sessions, planning, issue writing and architecture reviews must read
the relevant subfolder context themselves.** Subfolder `CLAUDE.md` files and
path-scoped rules only load once a file in that folder is read or edited, and
these sessions often finish before touching any. Before the first question,
read `analysis/CLAUDE.md` and/or `web/CLAUDE.md` for every area the topic
touches, plus any `.claude/rules/` file covering it.

## Architecture at a glance

- **`analysis/`** — Python batch jobs on GitHub Actions: the daily scoring run
  and the weekly catalog refresh. Writes to Postgres.
- **`web/`** — C# / ASP.NET Core MVC: reads the latest run, renders the D3 map;
  one narrow request-scoped Steam path for on-demand fetches.
- The two sides integrate **only** through the shared Postgres database
  (Supabase) and never call each other (ADR-005). Logic needed on both sides is
  ported, not shared — see `.claude/rules/`.
- Data comes from the public Steam Web API (`docs/steam-web-api.md`).
- Hosting: Azure App Service F1 for the web app, Supabase for Postgres, GitHub
  Actions for scheduling, CI and deploy (RFC-002).

## Working rules

Full rationale and dated history in `docs/methodology.md`.

- **TDD in strict cycles**: one red test asserting one behavior (an edge case
  gets its own red before any guard code), minimum code to green, refactor,
  commit. Expected values are worked out independently, never by re-running the
  formula under test. TDD covers domain logic; framework glue stays untested by
  design (ADR-006).
- **One conventional commit per cycle** (`feat(analysis):`, `test(web):`,
  `docs:`…), never batched. Docs follow the same rule: one commit per topic.
  When a change adapts existing code for a new feature, consider `refactor:`
  over `feat:`.
- **Push once per completed feature**, meaning a coherent, user-visible state:
  any push to `main` touching `web/` deploys to production, so commits that
  would ship a visibly broken page wait for the one that fixes it.
- **Readability over cleverness.** Clear names, explicit intermediate
  variables, plain control flow. Optimise only against a measured need; mention
  optimisation opportunities instead of applying them.
- **Fix exactly what was agreed.** Adjacent problems noticed along the way are
  reported, not fixed unasked.
- **Verify end to end before closing an issue**: a live pipeline run against
  Steam and Postgres, and for UI work a scripted headless-browser check.
- **Decisions are interviewed** (grill-me) and grounded in production data or a
  live call to any external endpoint the design leans on — never assumed.
- Where work deviates from an issue's acceptance criteria, write the deviation
  and its reason onto the issue.

## Decision records

- `adr/` — decisions that shape the system and are expensive to reverse.
  `rfc/` — pragmatic choices expected to be revisited. `docs/` — reference
  notes. Each folder's README lists its records.
- Records are **amended with a dated section**, never silently edited. An
  amendment prompted by implementation evidence lands as its own commit before
  the code.
- After any rename or renumbering, rewrite every reference in place — no
  old-to-new mapping notes, except where history can't be edited.

## Windows and PowerShell

- Edit files with the Edit/Write tools. Never round-trip a file through
  `Get-Content`/`WriteAllText`: PowerShell 5.1 decodes UTF-8 as ANSI and
  corrupts characters like em dashes.
- Commit messages go through a file: `git commit -F <file>`. Inline `-m` with
  double quotes gets split into pathspecs.
- Stage files explicitly by path, never `git add <dir>` or `git add .`.
- `gh secret set` takes the value with `--body`, never through a pipe.

## Secrets

Values propagate by reference (read from the local env var into each target),
never through chat, logs or echoed commands.

| Secret | Lives in | Used by |
|---|---|---|
| `SUPABASE_DB_URL` | GitHub Actions secret, local user env var, Azure app setting | Every job and the web app — rotate all three together |
| `STEAM_API_KEY` | GitHub Actions secret, local user env var | Only `weekly-catalog-refresh.yml` |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | GitHub Actions secret | `deploy-web.yml` |

Rotate the Supabase password with **alphanumeric characters only**: a
special-character password once produced a pooler credential that only the
newest client libraries could authenticate against. Allow 1–2 minutes of pooler
propagation after a reset. CI-side experiments run from a throwaway branch with
`gh workflow run <workflow> --ref <branch>`, never by pushing debug code to
`main`.

If the Azure hosting ever stops working, the options discussed so far are
converting the subscription to Pay-As-You-Go while staying on F1, Render.com,
Oracle Cloud Always Free, or Google Cloud Run (RFC-002).

## Ending a session

Before calling a session done, bring the docs in line with what happened, one
commit per topic:

- the `CLAUDE.md` that owns any area whose rules or open items changed;
- `docs/history.md` if something shipped;
- a new row in `docs/methodology.md`'s evolution table for any process change;
- `README.md` if the product visibly changed.
