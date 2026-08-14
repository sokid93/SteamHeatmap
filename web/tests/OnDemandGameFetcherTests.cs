using SteamHeatmap.Web.Domain;

namespace SteamHeatmap.Web.Tests;

public class FakeOnDemandSteamClient : IOnDemandSteamClient
{
    public int TotalReviews { get; set; }
    public string? Name { get; set; } = "A Game";
    public Dictionary<string, int> LanguageCounts { get; } = new();

    public Task<int> GetTotalReviewCount(int appId) => Task.FromResult(TotalReviews);

    public Task<string?> GetAppName(int appId) => Task.FromResult(Name);

    public Task<int> GetLanguageReviewCount(int appId, string languageCode) =>
        Task.FromResult(LanguageCounts.GetValueOrDefault(languageCode, 0));
}

public class FakeOnDemandRepository : IOnDemandRepository
{
    private readonly (int RunId, IReadOnlyDictionary<string, double> Baselines)? _context;

    public List<(int AppId, string Name, int RunId, IReadOnlyList<RegionScoreResult> Scores)> PersistedCalls { get; } = new();

    public FakeOnDemandRepository((int RunId, IReadOnlyDictionary<string, double> Baselines)? context) =>
        _context = context;

    public Task<(int RunId, IReadOnlyDictionary<string, double> Baselines)?> GetLatestRunContext() =>
        Task.FromResult(_context);

    public Task Persist(int appId, string name, int runId, IReadOnlyList<RegionScoreResult> scores)
    {
        PersistedCalls.Add((appId, name, runId, scores));
        return Task.CompletedTask;
    }
}

public class OnDemandGameFetcherTests
{
    private static readonly IReadOnlyDictionary<string, double> OneRegionBaseline =
        new Dictionary<string, double> { ["japanese"] = 0.02 };

    [Fact]
    public async Task NoRunYetMeansNotEnoughReviews()
    {
        var repository = new FakeOnDemandRepository(context: null);
        var fetcher = new OnDemandGameFetcher(new FakeOnDemandSteamClient(), repository);

        var result = await fetcher.Fetch(appId: 730);

        Assert.False(result.HasEnoughReviews);
        Assert.Empty(repository.PersistedCalls);
    }

    [Fact]
    public async Task ZeroTotalReviewsMeansNotEnoughReviewsAndIsNotPersisted()
    {
        var steam = new FakeOnDemandSteamClient { TotalReviews = 0 };
        var repository = new FakeOnDemandRepository((1, OneRegionBaseline));
        var fetcher = new OnDemandGameFetcher(steam, repository);

        var result = await fetcher.Fetch(appId: 730);

        Assert.False(result.HasEnoughReviews);
        Assert.Empty(repository.PersistedCalls);
    }

    [Fact]
    public async Task MissingAppNameMeansNotEnoughReviews()
    {
        // A delisted/removed app: appreviews may still answer, appdetails won't.
        var steam = new FakeOnDemandSteamClient { TotalReviews = 500, Name = null };
        var repository = new FakeOnDemandRepository((1, OneRegionBaseline));
        var fetcher = new OnDemandGameFetcher(steam, repository);

        var result = await fetcher.Fetch(appId: 730);

        Assert.False(result.HasEnoughReviews);
        Assert.Empty(repository.PersistedCalls);
    }

    [Fact]
    public async Task NoRegionReachesTheRankingThresholdMeansNotEnoughReviews()
    {
        var steam = new FakeOnDemandSteamClient { TotalReviews = 500 };
        steam.LanguageCounts["japanese"] = 49; // ADR-013: 50 is the floor
        var repository = new FakeOnDemandRepository((1, OneRegionBaseline));
        var fetcher = new OnDemandGameFetcher(steam, repository);

        var result = await fetcher.Fetch(appId: 730);

        Assert.False(result.HasEnoughReviews);
        Assert.Empty(repository.PersistedCalls);
    }

    [Fact]
    public async Task EligibleRegionIsScoredAndPersistedUnderTheCurrentRun()
    {
        var steam = new FakeOnDemandSteamClient { TotalReviews = 1000, Name = "Some Game" };
        steam.LanguageCounts["japanese"] = 100; // share 0.1, well above the 0.02 baseline
        var baselines = new Dictionary<string, double> { ["japanese"] = 0.02 };
        var repository = new FakeOnDemandRepository((42, baselines));
        var fetcher = new OnDemandGameFetcher(steam, repository);

        var result = await fetcher.Fetch(appId: 730);

        Assert.True(result.HasEnoughReviews);
        Assert.Equal("Some Game", result.GameName);
        var score = Assert.Single(result.RegionScores);
        Assert.Equal("japanese", score.RegionCode);
        Assert.Equal(1000, score.TotalReviews);
        Assert.Equal(100, score.InLanguageReviews);
        Assert.True(score.Concentration > 1.0); // above baseline

        var persisted = Assert.Single(repository.PersistedCalls);
        Assert.Equal(730, persisted.AppId);
        Assert.Equal("Some Game", persisted.Name);
        Assert.Equal(42, persisted.RunId);
        Assert.Same(result.RegionScores, persisted.Scores);
    }

    [Fact]
    public async Task RegionsBelowThresholdAreExcludedButDoNotBlockEligibleOnes()
    {
        var steam = new FakeOnDemandSteamClient { TotalReviews = 1000 };
        steam.LanguageCounts["japanese"] = 100; // eligible
        steam.LanguageCounts["french"] = 10; // below the 50-review floor
        var baselines = new Dictionary<string, double> { ["japanese"] = 0.02, ["french"] = 0.02 };
        var repository = new FakeOnDemandRepository((1, baselines));
        var fetcher = new OnDemandGameFetcher(steam, repository);

        var result = await fetcher.Fetch(appId: 730);

        Assert.True(result.HasEnoughReviews);
        var score = Assert.Single(result.RegionScores);
        Assert.Equal("japanese", score.RegionCode);
    }
}
