# ADR-009: C# / ASP.NET Core MVC as the primary web stack

## Context
Developer's background is C#/.NET (strongest), with working familiarity in Python and Java. Coming from game development, new to web development specifically. Wants MVC architecture and TDD.

## Decision
ASP.NET Core MVC as the main web framework and language, since it gives a genuine first-class MVC framework, mature TDD tooling (xUnit/NUnit + Moq), and lets the developer learn "web as a new domain" without also learning a new primary language. Java was ruled out as functionally redundant with C# for this project (same strengths, no unique advantage). Python is used specifically and only for the analysis/batch layer (ADR-006), not as an alternative primary stack.

## Alternatives rejected
- Python/Django or Flask as primary: strong data ecosystem, but developer explicitly wants C# as the main language, with Python exposure scoped to the analysis step only.
- Java/Spring Boot: same capabilities as C#/.NET for this project, no reason to pick over the developer's stronger language.

## Consequences
- None beyond what's already covered in ADR-006 (Python integration) and ADR-008 (testing/structure approach).
