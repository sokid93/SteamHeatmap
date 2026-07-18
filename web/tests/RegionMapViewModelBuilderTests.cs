using SteamHeatmap.Web.Domain;

namespace SteamHeatmap.Web.Tests;

public class FakeRankingRepository : IRankingRepository
{
    private readonly IReadOnlyList<RegionGameScore> _scores;

    public FakeRankingRepository(IReadOnlyList<RegionGameScore> scores) => _scores = scores;

    public Task<IReadOnlyList<RegionGameScore>> GetLatestRegionScores() => Task.FromResult(_scores);
}

public class RegionMapViewModelBuilderTests
{
    [Fact]
    public async Task ShapesSingleScoreRowIntoOneRegionWithItsGame()
    {
        var repository = new FakeRankingRepository(new[]
        {
            new RegionGameScore(
                RegionCode: "english",
                RegionDisplayName: "English-speaking",
                MemberCountries: new[] { "US", "GB", "CA", "AU" },
                Blended: true,
                AppId: 730,
                GameName: "Counter-Strike 2",
                Concentration: 0.81,
                MostPlayedRank: 1),
        });
        var builder = new RegionMapViewModelBuilder(repository);

        var viewModel = await builder.Build();

        var region = Assert.Single(viewModel.Regions);
        Assert.Equal("English-speaking", region.DisplayName);
        Assert.True(region.Blended);
        Assert.Equal(new[] { "US", "GB", "CA", "AU" }, region.MemberCountries);
        var game = Assert.Single(region.Games);
        Assert.Equal("Counter-Strike 2", game.Name);
        Assert.Equal(0.81, game.Concentration, precision: 3);
    }

    [Fact]
    public async Task RanksGamesWithinARegionByConcentrationDescending()
    {
        var repository = new FakeRankingRepository(new[]
        {
            EnglishScore(appId: 730, gameName: "Counter-Strike 2", concentration: 0.81),
            EnglishScore(appId: 570, gameName: "Dota 2", concentration: 1.35),
        });
        var builder = new RegionMapViewModelBuilder(repository);

        var viewModel = await builder.Build();

        var region = Assert.Single(viewModel.Regions);
        Assert.Equal(new[] { "Dota 2", "Counter-Strike 2" }, region.Games.Select(g => g.Name));
    }

    [Fact]
    public async Task GameEntryLinksToItsSteamStorePage()
    {
        var repository = new FakeRankingRepository(new[]
        {
            EnglishScore(appId: 730, gameName: "Counter-Strike 2", concentration: 0.81),
        });
        var builder = new RegionMapViewModelBuilder(repository);

        var viewModel = await builder.Build();

        var game = Assert.Single(Assert.Single(viewModel.Regions).Games);
        Assert.Equal("https://store.steampowered.com/app/730/", game.StoreUrl);
    }

    [Fact]
    public async Task KeepsOnlyTheTenHighestRankedGamesPerRegion()
    {
        var elevenGames = Enumerable.Range(1, 11)
            .Select(i => EnglishScore(appId: i, gameName: $"Game {i}", concentration: i))
            .ToArray();
        var builder = new RegionMapViewModelBuilder(new FakeRankingRepository(elevenGames));

        var viewModel = await builder.Build();

        var region = Assert.Single(viewModel.Regions);
        Assert.Equal(10, region.Games.Count);
        Assert.DoesNotContain("Game 1", region.Games.Select(g => g.Name)); // the lowest ranked
    }

    [Fact]
    public async Task RegionExposesItsTopGameConcentrationForMapShading()
    {
        var repository = new FakeRankingRepository(new[]
        {
            EnglishScore(appId: 730, gameName: "Counter-Strike 2", concentration: 0.81),
            EnglishScore(appId: 570, gameName: "Dota 2", concentration: 1.35),
        });
        var builder = new RegionMapViewModelBuilder(repository);

        var viewModel = await builder.Build();

        Assert.Equal(1.35, Assert.Single(viewModel.Regions).TopConcentration, precision: 3);
    }

    [Fact]
    public void RegionWithNoGamesHasZeroTopConcentration()
    {
        var region = new RegionEntry(
            Code: "english",
            DisplayName: "English-speaking",
            MemberCountries: new[] { "US" },
            Blended: false,
            Games: Array.Empty<GameEntry>());

        Assert.Equal(0, region.TopConcentration);
    }

    [Fact]
    public async Task ExposesTrackedGamesOrderedByMostPlayedRank()
    {
        var repository = new FakeRankingRepository(new[]
        {
            EnglishScore(appId: 570, gameName: "Dota 2", concentration: 1.35, mostPlayedRank: 2),
            EnglishScore(appId: 730, gameName: "Counter-Strike 2", concentration: 0.81, mostPlayedRank: 1),
        });
        var builder = new RegionMapViewModelBuilder(repository);

        var viewModel = await builder.Build();

        Assert.Equal(new[] { "Counter-Strike 2", "Dota 2" }, viewModel.Games.Select(g => g.Name));
    }

    private static RegionGameScore EnglishScore(
        int appId, string gameName, double concentration, int? mostPlayedRank = 1) =>
        new(
            RegionCode: "english",
            RegionDisplayName: "English-speaking",
            MemberCountries: new[] { "US", "GB", "CA", "AU" },
            Blended: true,
            AppId: appId,
            GameName: gameName,
            Concentration: concentration,
            MostPlayedRank: mostPlayedRank);
}
