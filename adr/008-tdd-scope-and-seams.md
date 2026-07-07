# ADR-008: TDD scope limited to domain-level logic; single project with disciplined folder separation

## Context
The developer wants TDD as the working methodology but is not deeply experienced with mocking, and explicitly does not want a multi-project (Clean/Onion Architecture) C# solution structure, preferring to maintain decoupling through discipline rather than compiler-enforced project boundaries.

## Decision
- Unit-test only domain-level logic (Wilson scoring, region mapping/baseline computation, ranking aggregation) — not controllers, EF Core/repository wiring, or the Steam API integration itself directly.
- The only fake/mock boundary needed is the Steam-client seam (`ISteamClient` in C# / a `SteamClient` protocol in Python), fed by recorded fixture responses — never the real API in tests.
- Integration and end-to-end tests are explicitly deferred until a concrete need arises, not built preemptively.
- Single C# project, folder-based separation between domain/infrastructure/web layers, relying on developer discipline rather than separate assemblies.

## Alternatives rejected
- Multi-project Clean/Onion Architecture (Domain/Infrastructure/Web/Tests as separate projects): would compiler-enforce the decoupling, but explicitly rejected in favor of single-project discipline.

## Consequences
- Requires ongoing discipline to avoid DB/API calls leaking into logic meant to stay pure — no structural enforcement, by choice.
- See the `tdd` skill (`tests.md`, `mocking.md`) for the concrete good/bad test patterns agreed for this project.
