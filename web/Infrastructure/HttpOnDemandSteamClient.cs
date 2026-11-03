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
    // Valve's documented replacement for the retired store.steampowered.com/
    // appreviews: keyless, one app and one language per call, same counts.
    private const string AppReviewsUrl = "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/";

    // Enum values: purchase_type 1 = all purchases (appreviews' purchase_type=all,
    // so key activations count); review_type 0 = all, the only value for which
    // query_summary carries total_reviews.
    private const int PurchaseTypeAll = 1;
    private const int ReviewTypeAll = 0;

    private readonly HttpClient _http;

    public HttpOnDemandSteamClient(HttpClient http) => _http = http;

    public Task<int> GetTotalReviewCount(int appId) => QueryTotalReviews(appId, "all");

    public Task<int> GetLanguageReviewCount(int appId, string languageCode) => QueryTotalReviews(appId, languageCode);

    private async Task<int> QueryTotalReviews(int appId, string language)
    {
        var request = JsonSerializer.Serialize(new
        {
            appid = appId,
            languages = new[] { language },
            // Only the count is needed, but 0 means "default" (20 full reviews).
            num_per_page = 1,
            purchase_type = PurchaseTypeAll,
            review_type = ReviewTypeAll,
        });
        using var document = await GetJson($"{AppReviewsUrl}?input_json={Uri.EscapeDataString(request)}");
        // Some apps (e.g. ones without a public store page) get an empty
        // response: no usable reviews.
        if (!document.RootElement.GetProperty("response").TryGetProperty("query_summary", out var summary))
            return 0;
        return summary.GetProperty("total_reviews").GetInt32();
    }

    public async Task<string?> GetAppName(int appId)
    {
        using var document = await GetJson($"https://store.steampowered.com/api/appdetails?appids={appId}&filters=basic");
        var entry = document.RootElement.GetProperty(appId.ToString());
        if (!entry.GetProperty("success").GetBoolean()) return null;
        return entry.GetProperty("data").GetProperty("name").GetString();
    }

    private async Task<JsonDocument> GetJson(string url)
    {
        using var response = await _http.GetAsync(url);
        response.EnsureSuccessStatusCode();
        // A retired endpoint can still answer 200 — appreviews redirects to the
        // store's HTML homepage — so a successful status alone proves nothing.
        var mediaType = response.Content.Headers.ContentType?.MediaType;
        if (mediaType is null || !mediaType.Contains("json"))
            throw new UnexpectedSteamResponseException(url, response, mediaType);
        return JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    }
}

// Steam answered successfully but not with JSON: the endpoint has most likely
// been changed or retired.
public class UnexpectedSteamResponseException(string url, HttpResponseMessage response, string? mediaType)
    : Exception(
        $"{url.Split('?')[0]} answered {(int)response.StatusCode} with {mediaType ?? "no content type"}" +
        RedirectNote(url, response) +
        " instead of JSON. Steam may have changed or retired this endpoint.")
{
    private static string RedirectNote(string url, HttpResponseMessage response)
    {
        var final = response.RequestMessage?.RequestUri;
        if (final is null || final.GetLeftPart(UriPartial.Path) == url.Split('?')[0]) return "";
        return $", after a redirect to {final.GetLeftPart(UriPartial.Path)}";
    }
}
