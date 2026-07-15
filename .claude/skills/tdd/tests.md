# What good and bad tests look like

Examples below are shown in both C# (xUnit) and Python (pytest), since this project uses both. The principle is language-agnostic: test through the real public interface, never through a side channel into internals.

## Good: tests observable behavior through the public interface

**C# (xUnit)**
```csharp
[Fact]
public void RankingService_ScoresGameByWilsonLowerBound()
{
    var reviews = new LanguageReviewCounts(total: 5000, inLanguage: 2000);

    var score = RankingService.ComputeRegionScore(reviews);

    Assert.Equal(0.378, score, precision: 3); // known-good value, computed independently
}
```

**Python (pytest)**
```python
def test_wilson_score_penalizes_small_samples():
    noisy_small_sample = LanguageReviewCounts(total=12, in_language=8)
    solid_large_sample = LanguageReviewCounts(total=5000, in_language=2000)

    noisy_score = compute_region_score(noisy_small_sample)
    solid_score = compute_region_score(solid_large_sample)

    assert noisy_score < solid_score  # observable outcome, not implementation
```

Both examples call the real function/method under test and assert on what it returns — nothing here knows or cares how the Wilson calculation is implemented internally.

## Bad: implementation-coupled

**C# (xUnit)**
```csharp
// BAD: reaches into a private/internal collaborator instead of the public result
[Fact]
public void RankingService_CallsWilsonCalculator()
{
    var mockCalculator = new Mock<IWilsonCalculator>();
    var service = new RankingService(mockCalculator.Object);

    service.ComputeRegionScore(reviews);

    mockCalculator.Verify(c => c.Calculate(It.IsAny<int>(), It.IsAny<int>()), Times.Once);
}
```
This breaks the moment you refactor `RankingService` to compute the score a different way internally, even though the actual behavior (the score it returns) hasn't changed. The tell is always the same: the test fails on a refactor that changed nothing a user or caller could observe.

**Python (pytest)**
```python
# BAD: queries the database directly instead of going through the repository interface
def test_save_game_ranking():
    save_game_ranking(game_id=123, score=0.42)

    cursor.execute("SELECT score FROM rankings WHERE game_id = 123")
    row = cursor.fetchone()
    assert row[0] == 0.42
```
Prefer calling `get_game_ranking(game_id=123)` through the same repository interface the rest of the app uses — that's the seam, not the raw SQL.

## Bad: tautological

```python
# BAD: recomputes the expected value the same way the code does
def test_add():
    a, b = 2, 3
    assert add(a, b) == a + b  # passes by construction, can never fail meaningfully
```
The expected value must come from an independent source — a literal number worked out by hand, a documented spec value, a known-good fixture — never the same formula the code under test uses.

## Bad: horizontal slicing

Writing every test file for the whole ranking module up front, then writing all the implementation afterward, is the anti-pattern to avoid here specifically. Given this project's scope (Wilson scoring, region mapping, top-N aggregation), work one vertical slice at a time:

1. One test: "a game with 0 reviews in a language scores 0" → make it pass
2. One test: "a game with equal total and in-language reviews scores near 1" → make it pass
3. One test: "a small sample scores lower than a large sample at the same raw percentage" → make it pass

Each cycle should teach you something about the next test to write — not be planned out in bulk beforehand.
