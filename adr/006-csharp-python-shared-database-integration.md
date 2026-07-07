# ADR-006: C# (web app) and Python (analysis job) integrate only via a shared Postgres database

## Context
The developer wants C# (ASP.NET Core MVC) as the primary language and web framework, but wants exposure to Python's data-analysis ecosystem for the daily aggregation/scoring step (Wilson score, region-baseline computation). This requires the two languages to cooperate without either becoming the primary architecture.

## Decision
Python runs as an independent, scheduled batch process (GitHub Actions cron) that reads raw Steam data and writes fully processed results (rankings, scores) into shared Postgres tables. The C# web app only ever reads from those tables — it never invokes Python directly, and Python never calls into the C# app.

## Alternatives rejected
- C# invoking Python as a subprocess: tighter coupling, harder to test each side independently, unnecessary for a daily-batch cadence.
- Python as a small internal HTTP API called by C#: overkill for batch/offline processing; would only make sense for on-demand/live analysis, which is not the MVP shape.

## Consequences
- Two independent codebases/dependency ecosystems/test suites (xUnit for C#, pytest for Python) in one monorepo (ADR-011).
- Schema changes must be coordinated manually between the two sides (no shared ORM/type system linking them) — acceptable at this scale.
