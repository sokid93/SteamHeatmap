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
    // store.steampowered.com/appreviews was retired in late September 2026
    // (it now redirects to the store homepage); GetItems replaces it. See the
    // ADR-013 amendment for how its counts differ.
    private const string GetItemsUrl = "https://api.steampowered.com/IStoreBrowseService/GetItems/v1/";

    private readonly HttpClient _http;

    public HttpOnDemandSteamClient(HttpClient http) => _http = http;

    public async Task<int> GetTotalReviewCount(int appId)
    {
        // The total is the same from any language's point of view.
        var reviews = await GetReviews(appId, "english");
        // An app Steam returns no reviews block for has no usable reviews.
        if (reviews is null) return 0;
        return reviews.Value.GetProperty("summary_filtered").GetProperty("review_count").GetInt32();
    }

    public async Task<int> GetLanguageReviewCount(int appId, string languageCode)
    {
        var reviews = await GetReviews(appId, languageCode);
        // Steam omits a language's count below 200 reviews. That is below
        // MinReviewsToRank either way, so it reads as zero here — unlike the
        // daily pipeline, this path computes no baseline that could tell them apart.
        if (reviews is null || !reviews.Value.TryGetProperty("summary_language_specific", out var specific))
            return 0;
        return specific.GetProperty("review_count").GetInt32();
    }

    private async Task<JsonElement?> GetReviews(int appId, string language)
    {
        var request = JsonSerializer.Serialize(new
        {
            ids = new[] { new { appid = appId } },
            context = new { language, country_code = "US" },
            data_request = new { include_reviews = true },
        });
        using var document = await GetJson($"{GetItemsUrl}?input_json={Uri.EscapeDataString(request)}");
        var item = document.RootElement.GetProperty("response").GetProperty("store_items")[0];
        // Clone: the element must outlive the document disposed on return.
        return item.TryGetProperty("reviews", out var reviews) ? reviews.Clone() : null;
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
