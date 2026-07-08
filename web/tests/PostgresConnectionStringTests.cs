using SteamHeatmap.Web.Infrastructure;

namespace SteamHeatmap.Web.Tests;

public class PostgresConnectionStringTests
{
    [Fact]
    public void ConvertsPostgresqlUriToNpgsqlKeywordFormat()
    {
        var uri = "postgresql://user.project:s3cret@pooler.example.com:5432/postgres";

        var result = PostgresConnectionString.FromUri(uri);

        Assert.Equal(
            "Host=pooler.example.com;Port=5432;Username=user.project;Password=s3cret;Database=postgres",
            result);
    }

    [Fact]
    public void PassesThroughKeywordFormatUnchanged()
    {
        var keywordFormat = "Host=localhost;Username=postgres;Password=x;Database=postgres";

        var result = PostgresConnectionString.FromUri(keywordFormat);

        Assert.Equal(keywordFormat, result);
    }
}
