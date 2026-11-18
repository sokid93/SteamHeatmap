# web/ — C# ASP.NET Core MVC app

Reads the latest run from Postgres and renders the map. Single project; layers
are separated by folder and by discipline, not by assembly (ADR-006, ADR-007).

## Layout

- `Domain/` — pure logic under TDD: `RegionMapViewModelBuilder` (featured game,
  per-game scores, eligibility, top-10 per region, rank-ordered game list),
  `CatalogSearchViewModelBuilder`, `OnDemandGameFetcher`, `OnDemandScoring`,
  and the repository/client interfaces they depend on.
- `Infrastructure/` — `Postgres*Repository` and `HttpOnDemandSteamClient`.
  Untested by design; the interfaces in `Domain/` are the faked seams.
- `Controllers/HomeController.cs` — `Index`, `GET SearchCatalog?q=`,
  `POST FetchGame(appId)`.
- `Views/` — Razor. `wwwroot/js/map.js` exposes `initRegionMap(...)` and only
  paints and transitions state: every decision arrives precomputed in the view
  model.

## How data reaches the page

- The full latest-run dataset is **embedded in the page**; hovering, clicking
  and searching tracked games never call the server (ADR-010). This also hides
  F1 cold starts after first paint.
- Only two endpoints exist, both for out-of-catalog search (ADR-011):
  - `SearchCatalog` — substring match on `steam_apps`, ranked exact > prefix >
    contains, capped at 10. `map.js` calls it 250 ms after typing stops, only
    when local matches are fewer than 10.
  - `FetchGame` — the on-demand path: ~29 Steam calls in parallel, scored with
    `OnDemandScoring` against the latest run's persisted baselines, upserted
    into that same run so every visitor sees it. Zero reviews or no eligible
    region returns "not enough reviews" and persists nothing.
- An on-demand game's own heatmap works immediately, but it only appears in
  other regions' top-10 lists after the next daily run. Intended, not a bug.

## Map encoding (ADR-010) and styling (RFC-004)

- One game at a time. Fill meanings: blue ramp = eligible score; neutral
  "tracked, no signal" = region tracked but nothing to show; darker neutral =
  outside the dataset. Log scale, clamped to [×⅛, ×8]; the hover popup always
  shows the real value.
- Colors and type are CSS custom properties in `site.css` — use the tokens,
  don't add raw values. Dark theme only. Manrope, self-hosted.
- Motion: exactly three CSS transitions (country hover, popup, search dropdown),
  130 ms, `prefers-reduced-motion` honored. Content swaps stay instant.
- WCAG AA for text and UI chrome is a hard requirement; contrast claims are
  measured, never eyeballed.
- The disclosures (language as proxy, no Valve affiliation) stay always
  visible.

## Testing, deploy and verification

- From `web/`: `dotnet test tests/SteamHeatmap.Web.Tests.csproj`. Tests fake
  the repositories and the Steam client.
- **Any push to `main` touching `web/` runs these tests and deploys to
  production** (`deploy-web.yml`). Hold commits that would leave the page
  visibly broken until the fix lands.
- UI work is verified in a headless browser before an issue closes:
  screenshots plus scripted hover/click assertions with `puppeteer-core`,
  installed in the scratchpad, against the local or live app. The machine's
  Chrome path is in `CLAUDE.local.md`.
- Expect a 15–30 s cold start on F1 after idle. A 500 right after a restart is
  the restart window — retry before diagnosing.

## Known gaps (not filed as issues)

- A failed GeoJSON fetch leaves "Loading map…" up indefinitely; no error state
  was ever scoped.
- The search dropdown fades in but not out: `map.js` dismisses it by clearing
  `innerHTML`.
- The font is self-hosted to avoid third-party requests, but D3 still loads
  from jsDelivr (RFC-003), so that goal is half-met.
- Blended regions are hard to see as a unit before hovering; the ×values could
  use a friendlier visual form.
- The deferred responsive pass will need to stack the map header bar
  (headline and search share a row).
- Deferred architecture candidate: `PostgresRankingRepository` reads columns by
  position, so reordering its `select` list breaks it silently.

## Decisions that apply here

ADR-005 (shared database), ADR-006 (test scope), ADR-007 (C# stack),
ADR-010 (map encoding), ADR-011 (out-of-catalog search), RFC-002 (hosting),
RFC-003 (Razor + CSS + D3), RFC-004 (visual identity).
