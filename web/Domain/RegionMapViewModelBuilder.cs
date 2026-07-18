namespace SteamHeatmap.Web.Domain;

public record GameEntry(int AppId, string Name, double Concentration)
{
    public string StoreUrl => $"https://store.steampowered.com/app/{AppId}/";
}

public record RegionEntry(
    string Code,
    string DisplayName,
    IReadOnlyList<string> MemberCountries,
    bool Blended,
    IReadOnlyList<GameEntry> Games)
{
    /// <summary>Drives the region's shading on the map.</summary>
    public double TopConcentration => Games.Count == 0 ? 0 : Games.Max(g => g.Concentration);
}

public record TrackedGameEntry(int AppId, string Name, int? MostPlayedRank);

public record RegionMapViewModel(
    IReadOnlyList<RegionEntry> Regions,
    IReadOnlyList<TrackedGameEntry> Games,
    IReadOnlyDictionary<int, IReadOnlyDictionary<string, double>> ConcentrationsByGame)
{
    /// <summary>The game whose heatmap the map shows on landing (ADR-014).</summary>
    public int? FeaturedAppId => Games.Count == 0 ? null : Games[0].AppId;
}

public class RegionMapViewModelBuilder
{
    private const int GamesShownPerRegion = 10;

    private readonly IRankingRepository _repository;

    public RegionMapViewModelBuilder(IRankingRepository repository) => _repository = repository;

    public async Task<RegionMapViewModel> Build()
    {
        var scores = await _repository.GetLatestRegionScores();

        var regions = scores
            .GroupBy(s => s.RegionCode)
            .Select(group =>
            {
                var first = group.First();
                return new RegionEntry(
                    Code: first.RegionCode,
                    DisplayName: first.RegionDisplayName,
                    MemberCountries: first.MemberCountries,
                    Blended: first.Blended,
                    Games: group
                        .OrderByDescending(s => s.Concentration)
                        .Take(GamesShownPerRegion)
                        .Select(s => new GameEntry(s.AppId, s.GameName, s.Concentration))
                        .ToList());
            })
            .ToList();

        var games = scores
            .OrderBy(s => s.MostPlayedRank ?? int.MaxValue)
            .GroupBy(s => s.AppId)
            .Select(group => group.First())
            .Select(s => new TrackedGameEntry(s.AppId, s.GameName, s.MostPlayedRank))
            .ToList();

        var concentrationsByGame = scores
            .GroupBy(s => s.AppId)
            .ToDictionary(
                group => group.Key,
                group => (IReadOnlyDictionary<string, double>)group
                    .ToDictionary(s => s.RegionCode, s => s.Concentration));

        return new RegionMapViewModel(regions, games, concentrationsByGame);
    }
}
