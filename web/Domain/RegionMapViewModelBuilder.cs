namespace SteamHeatmap.Web.Domain;

public record GameEntry(int AppId, string Name, double Concentration);

public record RegionEntry(
    string Code,
    string DisplayName,
    IReadOnlyList<string> MemberCountries,
    bool Blended,
    IReadOnlyList<GameEntry> Games);

public record RegionMapViewModel(IReadOnlyList<RegionEntry> Regions);

public class RegionMapViewModelBuilder
{
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
                        .Select(s => new GameEntry(s.AppId, s.GameName, s.Concentration))
                        .ToList());
            })
            .ToList();

        return new RegionMapViewModel(regions);
    }
}
