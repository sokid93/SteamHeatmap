using Npgsql;
using SteamHeatmap.Web.Domain;

namespace SteamHeatmap.Web.Infrastructure;

public class PostgresCatalogSearchRepository : ICatalogSearchRepository
{
    // Candidate cap before CatalogSearchViewModelBuilder's in-process ranking
    // narrows to the 10 actually shown — generous enough that a genuine
    // exact/prefix match is never pushed out by contains-only matches that
    // alphabetically sort ahead of it in the DB-side order.
    private const int CandidateLimit = 200;

    private readonly string _connectionString;

    public PostgresCatalogSearchRepository(string connectionString) => _connectionString = connectionString;

    public async Task<IReadOnlyList<CatalogEntry>> FindByNameSubstring(string query)
    {
        const string sql = """
            select app_id, name from steam_apps
            where name ilike @pattern
            order by name
            limit @limit
            """;

        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync();
        await using var command = new NpgsqlCommand(sql, connection);
        command.Parameters.AddWithValue("pattern", $"%{query}%");
        command.Parameters.AddWithValue("limit", CandidateLimit);
        await using var reader = await command.ExecuteReaderAsync();

        var results = new List<CatalogEntry>();
        while (await reader.ReadAsync())
            results.Add(new CatalogEntry(reader.GetInt32(0), reader.GetString(1)));
        return results;
    }
}
