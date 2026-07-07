# ADR-002: Language-to-region mapping, including blended regions

## Context
Steam's official language codes distinguish some geographically-specific variants (`spanish` = Spain vs `latam` = Latin America; `portuguese` = Portugal vs `brazilian` = Brazil), confirmed against Steam's official supported-languages list. Other languages (`english`, `german`, `french`, `schinese`/`tchinese`) have no such split and inherently represent multiple countries.

## Decision
Every Steam language code maps to whichever set of countries it actually represents:
- One-to-one where Steam's codes support it (Spain vs Latam Spanish, Portugal vs Brazil).
- A single blended "region" (e.g. English → merged US/UK/Canada/Australia/etc.) where no finer split is possible from this data source.

Blended regions are displayed on the map with the same visual treatment as single-country regions (chosen over excluding them from the map entirely), with a UI disclosure that this is a consequence of the language-as-proxy approach (ADR-001), and a note about what true per-country data could offer.

## Alternatives rejected
- Excluding un-splittable languages (English) from the map, showing them as a separate sidebar stat instead — rejected as it "takes chunks out of the map" and is less visually cohesive for a portfolio product.

## Consequences
- The map must support one visual entity spanning multiple countries' shapes, with a way to signal "these are grouped" (exact mechanism — shared color, hover-highlight of the group, etc. — deferred to implementation/design time).
- This is a general policy, not an English-specific hack — applies to every currently or future ambiguous language code.
