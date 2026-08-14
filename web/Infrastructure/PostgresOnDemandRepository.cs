using Npgsql;
using SteamHeatmap.Web.Domain;

namespace SteamHeatmap.Web.Infrastructure;

// Untested by design (ADR-008) — the seam faked in tests is
// IOnDemandRepository, not this implementation.
public class PostgresOnDemandRepository : IOnDemandRepository
{
    private readonly string _connectionString;

    public PostgresOnDemandRepository(string connectionString) => _connectionString = connectionString;

    public async Task<(int RunId, IReadOnlyDictionary<string, double> Baselines)?> GetLatestRunContext()
    {
        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync();

        int runId;
        await using (var runCommand = new NpgsqlCommand("select max(id) from runs", connection))
        {
            var result = await runCommand.ExecuteScalarAsync();
            if (result is null or DBNull) return null; // fresh install, no pipeline run yet
            runId = (int)(long)result;
        }

        var baselines = new Dictionary<string, double>();
        await using (var baselineCommand = new NpgsqlCommand(
            "select region_code, baseline_share from region_baselines where run_id = @runId", connection))
        {
            baselineCommand.Parameters.AddWithValue("runId", runId);
            await using var reader = await baselineCommand.ExecuteReaderAsync();
            while (await reader.ReadAsync())
                baselines[reader.GetString(0)] = reader.GetDouble(1);
        }

        return (runId, baselines);
    }

    public async Task Persist(int appId, string name, int runId, IReadOnlyList<RegionScoreResult> scores)
    {
        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync();
        await using var transaction = await connection.BeginTransactionAsync();

        // most_played_rank is left untouched on conflict: an on-demand fetch
        // never knows a real rank, and must not clobber one the daily
        // pipeline already set for this app_id.
        await using (var gameCommand = new NpgsqlCommand(
            """
            insert into games (app_id, name, most_played_rank, last_relevant_at)
            values (@appId, @name, null, now())
            on conflict (app_id) do update set
                name = excluded.name,
                last_relevant_at = excluded.last_relevant_at
            """, connection, transaction))
        {
            gameCommand.Parameters.AddWithValue("appId", appId);
            gameCommand.Parameters.AddWithValue("name", name);
            await gameCommand.ExecuteNonQueryAsync();
        }

        // Upsert, not a bare insert: re-searching the same game (or two
        // concurrent visitors searching it around the same time) must not
        // crash on the (run_id, app_id, region_code) primary key.
        foreach (var score in scores)
        {
            await using var scoreCommand = new NpgsqlCommand(
                """
                insert into region_scores
                    (run_id, app_id, region_code, total_reviews, in_language_reviews,
                     wilson_adjusted_share, concentration)
                values (@runId, @appId, @regionCode, @totalReviews, @inLanguageReviews,
                        @wilsonAdjustedShare, @concentration)
                on conflict (run_id, app_id, region_code) do update set
                    total_reviews = excluded.total_reviews,
                    in_language_reviews = excluded.in_language_reviews,
                    wilson_adjusted_share = excluded.wilson_adjusted_share,
                    concentration = excluded.concentration
                """, connection, transaction);
            scoreCommand.Parameters.AddWithValue("runId", runId);
            scoreCommand.Parameters.AddWithValue("appId", appId);
            scoreCommand.Parameters.AddWithValue("regionCode", score.RegionCode);
            scoreCommand.Parameters.AddWithValue("totalReviews", score.TotalReviews);
            scoreCommand.Parameters.AddWithValue("inLanguageReviews", score.InLanguageReviews);
            scoreCommand.Parameters.AddWithValue("wilsonAdjustedShare", score.WilsonAdjustedShare);
            scoreCommand.Parameters.AddWithValue("concentration", score.Concentration);
            await scoreCommand.ExecuteNonQueryAsync();
        }

        await transaction.CommitAsync();
    }
}
