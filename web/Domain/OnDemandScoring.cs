namespace SteamHeatmap.Web.Domain;

// Bit-for-bit port of analysis/steamheatmap/scoring.py's wilson_lower_bound
// and concentration_score (issue #27). Deliberately duplicated rather than
// shared across the C#/Python boundary — ADR-006 keeps the two runtimes
// independent — but the formulas and constant must stay identical, or a
// game scored on-demand would land on a different color than one scored by
// the daily pipeline for the same inputs. Covered by the same golden test
// values as analysis/tests/test_scoring.py.
public static class OnDemandScoring
{
    private const double Z95 = 1.959963985;

    public static double WilsonLowerBound(int inLanguageReviews, int totalReviews, double confidenceZ = Z95)
    {
        double n = totalReviews;
        double pHat = inLanguageReviews / n;
        double z = confidenceZ;

        var denominator = 1 + z * z / n;
        var center = pHat + z * z / (2 * n);
        var margin = z * Math.Sqrt((pHat * (1 - pHat) + z * z / (4 * n)) / n);

        return (center - margin) / denominator;
    }

    public static double ConcentrationScore(double wilsonAdjustedShare, double baselineShare) =>
        wilsonAdjustedShare / baselineShare;
}
