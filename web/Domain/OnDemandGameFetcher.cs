namespace SteamHeatmap.Web.Domain;

public record RegionScoreResult(
    string RegionCode, int TotalReviews, int InLanguageReviews, double WilsonAdjustedShare, double Concentration);

public record OnDemandFetchResult(bool HasEnoughReviews, string? GameName, IReadOnlyList<RegionScoreResult> RegionScores)
{
    public static OnDemandFetchResult NotEnoughReviews() => new(false, null, Array.Empty<RegionScoreResult>());

    public static OnDemandFetchResult Success(string gameName, IReadOnlyList<RegionScoreResult> scores) =>
        new(true, gameName, scores);
}

// #27's request-scoped Steam-calling seam (ADR-006 amendment), distinct from
// the daily batch job's SteamClient protocol in analysis/ — same public
// endpoints, parallel calls instead of ~3,100 sequential ones a day.
public interface IOnDemandSteamClient
{
    Task<int> GetTotalReviewCount(int appId);
    Task<int> GetLanguageReviewCount(int appId, string languageCode);
    Task<string?> GetAppName(int appId);
}

public interface IOnDemandRepository
{
    // Region codes double as Steam review-language codes throughout this
    // project (region_mapping.py's dict key serves both roles) — the keys of
    // Baselines are exactly the language codes to query Steam for.
    Task<(int RunId, IReadOnlyDictionary<string, double> Baselines)?> GetLatestRunContext();

    Task Persist(int appId, string name, int runId, IReadOnlyList<RegionScoreResult> scores);
}

public class OnDemandGameFetcher
{
    // ADR-013, mirrors analysis/steamheatmap/pipeline.py's MIN_REVIEWS_TO_RANK.
    private const int MinReviewsToRank = 50;

    private readonly IOnDemandSteamClient _steam;
    private readonly IOnDemandRepository _repository;

    public OnDemandGameFetcher(IOnDemandSteamClient steam, IOnDemandRepository repository)
    {
        _steam = steam;
        _repository = repository;
    }

    public async Task<OnDemandFetchResult> Fetch(int appId)
    {
        var context = await _repository.GetLatestRunContext();
        if (context is null) return OnDemandFetchResult.NotEnoughReviews();
        var (runId, baselines) = context.Value;

        // Fired together, not sequentially — ~29 independent Steam calls for
        // one game would otherwise cost seconds a visitor is actively
        // waiting on, unlike the daily batch job's background pacing.
        var totalReviewsTask = _steam.GetTotalReviewCount(appId);
        var nameTask = _steam.GetAppName(appId);
        var languageCountTasks = baselines.Keys.ToDictionary(
            region => region, region => _steam.GetLanguageReviewCount(appId, region));
        await Task.WhenAll(languageCountTasks.Values.Cast<Task>().Append(totalReviewsTask).Append(nameTask));

        var totalReviews = await totalReviewsTask;
        var name = await nameTask;
        if (totalReviews == 0 || name is null) return OnDemandFetchResult.NotEnoughReviews();

        var scores = new List<RegionScoreResult>();
        foreach (var (region, baseline) in baselines)
        {
            var inLanguageReviews = await languageCountTasks[region];
            if (inLanguageReviews < MinReviewsToRank) continue;

            var adjusted = OnDemandScoring.WilsonLowerBound(inLanguageReviews, totalReviews);
            scores.Add(new RegionScoreResult(
                region, totalReviews, inLanguageReviews, adjusted,
                OnDemandScoring.ConcentrationScore(adjusted, baseline)));
        }

        // A permanently-empty entry isn't worth a daily refetch (ADR-016) —
        // matches the daily pipeline excluding zero-in-language games too.
        if (scores.Count == 0) return OnDemandFetchResult.NotEnoughReviews();

        await _repository.Persist(appId, name, runId, scores);
        return OnDemandFetchResult.Success(name, scores);
    }
}
