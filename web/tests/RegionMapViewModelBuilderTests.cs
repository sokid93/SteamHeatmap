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
                MemberCountries: new[] { "US", "UK", "CA", "AU" },
                Blended: true,
                AppId: 730,
                GameName: "Counter-Strike 2",
                Concentration: 0.81),
        });
        var builder = new RegionMapViewModelBuilder(repository);

        var viewModel = await builder.Build();

        var region = Assert.Single(viewModel.Regions);
        Assert.Equal("English-speaking", region.DisplayName);
        Assert.True(region.Blended);
        Assert.Equal(new[] { "US", "UK", "CA", "AU" }, region.MemberCountries);
        var game = Assert.Single(region.Games);
        Assert.Equal("Counter-Strike 2", game.Name);
        Assert.Equal(0.81, game.Concentration, precision: 3);
    }
}
