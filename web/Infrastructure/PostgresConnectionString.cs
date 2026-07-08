namespace SteamHeatmap.Web.Infrastructure;

public static class PostgresConnectionString
{
    /// <summary>
    /// Npgsql only accepts keyword=value connection strings, while Supabase
    /// hands out postgresql:// URIs (which psycopg2 accepts directly).
    /// </summary>
    public static string FromUri(string connectionString)
    {
        if (!connectionString.StartsWith("postgresql://") && !connectionString.StartsWith("postgres://"))
        {
            return connectionString;
        }

        var uri = new Uri(connectionString);
        var userInfo = uri.UserInfo.Split(':', 2);
        var username = Uri.UnescapeDataString(userInfo[0]);
        var password = userInfo.Length > 1 ? Uri.UnescapeDataString(userInfo[1]) : "";
        var database = uri.AbsolutePath.TrimStart('/');

        return $"Host={uri.Host};Port={uri.Port};Username={username};Password={password};Database={database}";
    }
}
