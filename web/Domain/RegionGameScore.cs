namespace SteamHeatmap.Web.Domain;

public record RegionGameScore(
    string RegionCode,
    string RegionDisplayName,
    IReadOnlyList<string> MemberCountries,
    bool Blended,
    int AppId,
    string GameName,
    double Concentration);
