# ADR-007: Start on free-tier hosting, plan a deliberate later migration to a VPS

## Context
Budget-conscious portfolio project; wants to see it actually deployed without committing money up front, but expects to eventually run it on paid infrastructure with fewer platform-specific quirks (e.g. self-hosted Jenkins, no cron/scheduling limitations).

## Decision
- Web app: Azure App Service, Free (F1) tier. Confirmed limits: 60 CPU-min/day, apps sleep after 20 min idle (cold start ~5-15s on next request), no custom-domain SSL, shared/throttled infrastructure. Accepted as a bounded, cosmetic-only tradeoff.
- Database: Supabase (managed free Postgres) — independent of wherever compute is hosted, survives future migrations of the web/batch layers unchanged.
- Scheduling/CI: GitHub Actions (not Jenkins/TeamCity, which require self-hosting a server — deferred to the VPS stage, where the developer's existing Jenkins experience becomes a natural upgrade).
- Deployment to App Service avoids Docker for now, to prevent stacking Docker-as-a-new-concept onto D3/two-language-pipeline/GitHub Actions all in the same MVP push. Docker is deferred to the VPS migration.

## Alternatives rejected
- Cheap VPS from day one: simpler long-term, but reintroduces cost now, which conflicts with the stated budget constraint.
- Self-hosted Jenkins/TeamCity now: would require a persistent server just to host the CI tool, contradicting the free-tier-first decision.

## Consequences
- A deliberate migration to a VPS (with Docker and possibly self-hosted Jenkins) is an explicitly planned future step, not an afterthought — worth its own future ADR when it happens.
