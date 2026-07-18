using Npgsql;
using SteamHeatmap.Web.Domain;

namespace SteamHeatmap.Web.Infrastructure;

public class PostgresRankingRepository : IRankingRepository
{
    private readonly string _connectionString;

    public PostgresRankingRepository(string connectionString) => _connectionString = connectionString;

    public async Task<IReadOnlyList<RegionGameScore>> GetLatestRegionScores()
    {
        const string sql = """
            select r.code, r.display_name, r.member_countries, r.blended,
                   g.app_id, g.name, s.concentration, g.most_played_rank
            from region_scores s
            join regions r on r.code = s.region_code
            join games g on g.app_id = s.app_id
            where s.run_id = (select max(id) from runs)
            """;

        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync();
        await using var command = new NpgsqlCommand(sql, connection);
        await using var reader = await command.ExecuteReaderAsync();

        var scores = new List<RegionGameScore>();
        while (await reader.ReadAsync())
        {
            scores.Add(new RegionGameScore(
                RegionCode: reader.GetString(0),
                RegionDisplayName: reader.GetString(1),
                MemberCountries: reader.GetFieldValue<string[]>(2),
                Blended: reader.GetBoolean(3),
                AppId: reader.GetInt32(4),
                GameName: reader.GetString(5),
                Concentration: reader.GetDouble(6),
                MostPlayedRank: reader.IsDBNull(7) ? null : reader.GetInt32(7)));
        }

        return scores;
    }
}
