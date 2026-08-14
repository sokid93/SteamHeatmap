namespace SteamHeatmap.Web.Domain;

public record CatalogEntry(int AppId, string Name);

public interface ICatalogSearchRepository
{
    Task<IReadOnlyList<CatalogEntry>> FindByNameSubstring(string query);
}

public class CatalogSearchViewModelBuilder
{
    private readonly ICatalogSearchRepository _repository;

    public CatalogSearchViewModelBuilder(ICatalogSearchRepository repository) => _repository = repository;

    public async Task<IReadOnlyList<CatalogEntry>> Search(string query)
    {
        var trimmed = query.Trim();
        if (trimmed.Length == 0) return Array.Empty<CatalogEntry>();

        return await _repository.FindByNameSubstring(trimmed);
    }
}
