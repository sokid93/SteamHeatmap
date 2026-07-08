namespace SteamHeatmap.Web.Domain;

public interface IRankingRepository
{
    Task<IReadOnlyList<RegionGameScore>> GetLatestRegionScores();
}
