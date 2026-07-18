# ADR-010: Server-rendered Razor + plain CSS + D3.js, not a SPA framework

## Context
Developer have a strong opinion about using libraries and frameworks before they are proven useful, which initially raised concern about frontend libraries generally, but was not focused on useful single-purpose libraries. Wants "cool, smooth" visuals eventually, as this project is intended as a portfolio centerpiece.

## Decision
- Keep the web app genuinely server-rendered: Razor views, plain CSS (no Tailwind/Bootstrap), no React/Vue/SPA framework or build pipeline.
- Use D3.js specifically (not Leaflet) for the map/heatmap visualization, chosen deliberately over Leaflet's simpler choropleth-only ceiling because the developer wants the higher visual ceiling (custom, animated, "cool smooth" transitions) for portfolio purposes, and is relying on Claude's help to manage D3's steeper learning curve.

## Alternatives rejected
- Full SPA frontend (React/Vue) treating the ASP.NET Core app as a pure JSON API: more moving parts (build pipeline, CORS), not needed for the current scope; a possible future path if UI complexity grows significantly.
- Leaflet.js: simpler and sufficient for a basic choropleth, but capped well below the "cool smooth visuals" portfolio goal; rejected in favor of D3's higher ceiling.

## Consequences
- D3's steeper learning curve is accepted knowingly, with the expectation of hands-on guidance during implementation.
- Layout and non-map UI stays plain HTML/CSS/Razor; D3 is scoped specifically to the map widget, not the whole page.
