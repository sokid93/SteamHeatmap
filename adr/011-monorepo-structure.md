# ADR-011: Single monorepo containing both the C# web app and the Python analysis job

## Context
The project doubles as a portfolio piece; the developer wants it presentable as one unified, coherent project rather than scattered across repos.

## Decision
One Git repository, with the C# app and Python job living side-by-side (e.g. `/web` and `/analysis`), sharing one set of top-level documentation (`CONTEXT.md`, ADRs, README) despite being otherwise independent codebases connected only through the shared database (ADR-006).

## Alternatives rejected
- Two separate repositories, connected only via the shared DB schema as an implicit contract: stricter separation, but fragments documentation and the portfolio narrative across two places.

## Consequences
- Cross-cutting documentation (this file, the ADRs) lives once, at the repo root, rather than duplicated.
- The two codebases still don't share dependencies, build tooling, or a single test run — the monorepo is organizational, not a build-system merge.
