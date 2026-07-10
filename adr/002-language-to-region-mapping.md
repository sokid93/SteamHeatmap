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

## Concrete mapping (decided 2026-07-10, grill-me session for issue #4)

**Scope**: all 30 Steam review language codes are fetched and scored (~3,100 API calls/day, ~3% of the cap).

**Membership rule — "de-facto review language"**: each country belongs to exactly one region, the language its Steam users actually write reviews in:
- If the country's native language is a supported Steam review language, it belongs there (Germany → `german`, Indonesia → `indonesian`, the Maghreb → `arabic`).
- If not (Hindi, Tagalog, ...), the country joins the language its Steam users de facto review in (India, Philippines → `english`).
- Multilingual countries follow their majority language community (Belgium → `dutch`, Switzerland → `german`).

Rationale: reviews from these countries are already counted inside the blended language totals either way; the only choice is whether the country shares the color its own reviews helped produce. Member lists use ISO 3166-1 alpha-2 codes (so `GB`, not `UK`).

**Blended regions** (blended = true):

| Code | Members |
|---|---|
| english | US GB IE CA AU NZ IN PK BD PH SG MY ZA NG KE GH |
| latam | MX AR CO CL PE VE EC GT BO DO HN PY SV NI CR PA UY CU |
| arabic | SA AE EG IQ JO KW QA BH OM LB SY YE LY SD DZ MA TN |
| russian | RU BY KZ KG UZ TJ TM AM AZ |
| french | FR LU SN CI CM CD ML BF NE TG BJ GA CG HT |
| german | DE AT CH |
| dutch | NL BE |
| tchinese | TW HK MO |
| portuguese | PT AO MZ |
| greek | GR CY |
| romanian | RO MD |

**Single-country regions** (blended = false): schinese → CN, brazilian → BR, spanish → ES, italian → IT, japanese → JP, koreana → KR, polish → PL, turkish → TR, ukrainian → UA, czech → CZ, hungarian → HU, bulgarian → BG, danish → DK, finnish → FI, norwegian → NO, swedish → SE, thai → TH, vietnamese → VN, indonesian → ID.

Everything else stays gray on the map ("no data"), including genuinely mixed cases deliberately left out (Georgia). Ukraine maps to `ukrainian` and Moldova to `romanian` (native-if-supported beats the Russian sphere); Singapore reviews de facto in English, not `schinese`.
