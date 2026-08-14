namespace SteamHeatmap.Web.Domain;

public record CatalogEntry(int AppId, string Name);

public interface ICatalogSearchRepository
{
    Task<IReadOnlyList<CatalogEntry>> FindByNameSubstring(string query);
}

public class CatalogSearchViewModelBuilder
{
    // Matches #14's client-side typeahead cap, so the two search paths feel
    // like one consistent dropdown rather than two differently-sized ones.
    private const int MaxResults = 10;

    private readonly ICatalogSearchRepository _repository;

    public CatalogSearchViewModelBuilder(ICatalogSearchRepository repository) => _repository = repository;

    public async Task<IReadOnlyList<CatalogEntry>> Search(string query)
    {
        var trimmed = query.Trim();
        if (trimmed.Length == 0) return Array.Empty<CatalogEntry>();

        var candidates = await _repository.FindByNameSubstring(trimmed);
        return Rank(candidates, trimmed);
    }

    // The repository already narrows candidates to a substring match (SQL);
    // this ranks them so the entry you were probably typing toward surfaces
    // first instead of wherever the DB happened to order it.
    private static IReadOnlyList<CatalogEntry> Rank(IReadOnlyList<CatalogEntry> candidates, string query) =>
        candidates.OrderBy(entry => MatchTier(entry.Name, query)).Take(MaxResults).ToList();

    private static int MatchTier(string name, string query)
    {
        if (name.Equals(query, StringComparison.OrdinalIgnoreCase)) return 0;
        if (name.StartsWith(query, StringComparison.OrdinalIgnoreCase)) return 1;
        return 2;
    }
}
