# Mocking guidelines

Mocking exists to isolate the domain logic under test from things that are genuinely external (a real network call to Steam, a real database, real wall-clock time) — not to isolate every internal collaborator from every other. Over-mocking is how implementation-coupled tests happen.

## Design the interface to be easy to mock

**Easy to mock — dependency passed in, one job per method**

C#:
```csharp
public interface ISteamClient
{
    Task<IReadOnlyList<GameRanking>> GetTopGames(int count);
    Task<LanguageReviewCounts> GetReviewCounts(int appId, string languageCode);
}

public class RankingPipeline
{
    private readonly ISteamClient _steamClient;
    public RankingPipeline(ISteamClient steamClient) => _steamClient = steamClient;
    // ...
}
```

Python:
```python
class SteamClient(Protocol):
    def get_top_games(self, count: int) -> list[GameRanking]: ...
    def get_review_counts(self, app_id: int, language_code: str) -> LanguageReviewCounts: ...

def run_ranking_pipeline(steam_client: SteamClient) -> list[RegionRanking]:
    ...
```

**Hard to mock — the dependency constructs itself internally, so tests can't substitute anything**

C#:
```csharp
public class RankingPipeline
{
    public async Task<...> Run()
    {
        var client = new HttpClient(); // constructed internally — nothing to inject
        var response = await client.GetAsync("https://api.steampowered.com/...");
        // ...
    }
}
```

Python:
```python
def run_ranking_pipeline():
    response = requests.get("https://api.steampowered.com/...")  # same problem
```

In both "hard" cases, a test has no seam to substitute a fake at — it would have to patch a global or monkeypatch the HTTP library itself, which is exactly the implementation-coupled pattern `tests.md` warns about.

## Prefer SDK-style interfaces over one generic method

**Good — each capability is its own method, independently fakeable**
```csharp
public interface ISteamClient
{
    Task<IReadOnlyList<GameRanking>> GetTopGames(int count);
    Task<LanguageReviewCounts> GetReviewCounts(int appId, string languageCode);
}
```

**Bad — one generic passthrough forces conditional logic into every fake**
```csharp
public interface ISteamClient
{
    Task<string> Fetch(string endpoint, Dictionary<string, string> parameters);
}
```
A fake implementing the generic version has to branch on the endpoint string to decide what to return, which turns the fake itself into untested logic. SDK-style, one-method-per-capability interfaces keep each fake trivial.

## What to fake in this project, concretely

- `ISteamClient` / `SteamClient` protocol — fake it with canned `GameRanking`/`LanguageReviewCounts` fixtures (recorded once from real API responses, frozen as test data). Never call the real Steam API from a test.
- The Postgres/Supabase repository interface — fake it with an in-memory implementation for domain-layer tests. Real database round-trips belong in integration tests, which are explicitly out of scope for now (per the earlier decision to only unit-test domain logic).
- Do **not** fake the Wilson score math, the region-mapping logic, or any other pure domain calculation — those are exactly what the tests exist to verify. If you find yourself wanting to mock the thing you're testing, that's a sign the seam is drawn in the wrong place.

## The tell that you're over-mocking

If a test needs to mock more than one collaborator to get a single behavior under test, or if the mock setup is longer than the assertion, that's usually a sign the test has drifted from "verify observable behavior" toward "verify internal wiring." Step back and ask whether there's a higher, more public seam to test at instead.
