using SteamHeatmap.Web.Domain;

namespace SteamHeatmap.Web.Tests;

public class FakeCatalogSearchRepository : ICatalogSearchRepository
{
    private readonly IReadOnlyList<CatalogEntry> _entries;

    public FakeCatalogSearchRepository(IReadOnlyList<CatalogEntry> entries) => _entries = entries;

    public Task<IReadOnlyList<CatalogEntry>> FindByNameSubstring(string query) => Task.FromResult(_entries);
}

public class CatalogSearchViewModelBuilderTests
{
    [Fact]
    public async Task BlankQueryReturnsNoResults()
    {
        var builder = new CatalogSearchViewModelBuilder(new FakeCatalogSearchRepository(Array.Empty<CatalogEntry>()));

        var results = await builder.Search("   ");

        Assert.Empty(results);
    }

    [Fact]
    public async Task ExactNameMatchRanksAboveALongerMatch()
    {
        var repository = new FakeCatalogSearchRepository(new[]
        {
            new CatalogEntry(1, "Half-Life 2: Lost Coast"),
            new CatalogEntry(2, "Half-Life 2"),
        });
        var builder = new CatalogSearchViewModelBuilder(repository);

        var results = await builder.Search("Half-Life 2");

        Assert.Equal(new[] { "Half-Life 2", "Half-Life 2: Lost Coast" }, results.Select(r => r.Name));
    }

    [Fact]
    public async Task PrefixMatchRanksAboveAMidStringMatch()
    {
        var repository = new FakeCatalogSearchRepository(new[]
        {
            new CatalogEntry(1, "Super Dota Clone"),
            new CatalogEntry(2, "Dota 2"),
        });
        var builder = new CatalogSearchViewModelBuilder(repository);

        var results = await builder.Search("Dota");

        Assert.Equal(new[] { "Dota 2", "Super Dota Clone" }, results.Select(r => r.Name));
    }

    [Fact]
    public async Task CapsResultsAtTenToMatchTheEmbeddedTypeaheadsLimit()
    {
        var entries = Enumerable.Range(1, 15).Select(i => new CatalogEntry(i, $"Game {i}")).ToArray();
        var builder = new CatalogSearchViewModelBuilder(new FakeCatalogSearchRepository(entries));

        var results = await builder.Search("Game");

        Assert.Equal(10, results.Count);
    }
}
