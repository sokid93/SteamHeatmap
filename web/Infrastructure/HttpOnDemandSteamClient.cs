using System.Text.Json;
using SteamHeatmap.Web.Domain;

namespace SteamHeatmap.Web.Infrastructure;

// Real Steam Web API client for #27's request-scoped path. Untested by
// design (ADR-008) — the seam faked in tests is IOnDemandSteamClient, not
// this implementation. Same public, keyless endpoints as the daily
// pipeline's RequestsSteamClient (analysis/), called concurrently rather
// than once a day across ~100 games.
public class HttpOnDemandSteamClient : IOnDemandSteamClient
{
    private readonly HttpClient _http;

    public HttpOnDemandSteamClient(HttpClient http) => _http = http;

    public Task<int> GetTotalReviewCount(int appId) => QueryTotalReviews(appId, "all");

    public Task<int> GetLanguageReviewCount(int appId, string languageCode) => QueryTotalReviews(appId, languageCode);

    private async Task<int> QueryTotalReviews(int appId, string language)
    {
        var url = $"https://store.steampowered.com/appreviews/{appId}" +
                   $"?json=1&language={language}&num_per_page=0&purchase_type=all";
        using var response = await _http.GetAsync(url);
        response.EnsureSuccessStatusCode();
        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        return document.RootElement.GetProperty("query_summary").GetProperty("total_reviews").GetInt32();
    }

    public async Task<string?> GetAppName(int appId)
    {
        var url = $"https://store.steampowered.com/api/appdetails?appids={appId}&filters=basic";
        using var response = await _http.GetAsync(url);
        response.EnsureSuccessStatusCode();
        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        var entry = document.RootElement.GetProperty(appId.ToString());
        if (!entry.GetProperty("success").GetBoolean()) return null;
        return entry.GetProperty("data").GetProperty("name").GetString();
    }
}
