# Requests for comments

An RFC here records a pragmatic choice made to keep the product moving: a
scope limit, a hosting plan, a stack or styling preference. Each one is
reasoned and in force, but provisional — it is expected to be revisited when
the constraint behind it changes (budget, scale, a second page), and replacing
it would not force a rewrite of the system's core.

Decisions that shape the system and are expensive to reverse live in
[`adr/`](../adr/) instead.

| RFC | Choice | Revisit when |
|---|---|---|
| [RFC-001](001-top-n-scope.md) | Track the top ~100 most-played games, not the full catalog | Partly done: ADR-011 added search over the full catalog |
| [RFC-002](002-hosting-free-tier-then-vps.md) | Free-tier hosting first, VPS later | Free tier stops being enough, or the planned VPS migration starts |
| [RFC-003](003-primary-stack-csharp-dotnet.md) | C# / ASP.NET Core MVC as the primary stack | No trigger recorded |
| [RFC-004](004-frontend-razor-plain-css-d3.md) | Server-rendered Razor + plain CSS + D3, no SPA | UI complexity outgrows server rendering |
| [RFC-005](005-dark-steam-inspired-homepage-styling.md) | Dark, Steam-inspired homepage styling | A second page or the responsive pass |

These five were numbered as ADRs until 2026-11-18; the old-to-new mapping is
in [`adr/README.md`](../adr/README.md#renumbering-2026-11-18).
