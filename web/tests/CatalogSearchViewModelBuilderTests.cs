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
}
