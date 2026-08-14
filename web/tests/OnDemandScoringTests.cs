using SteamHeatmap.Web.Domain;

namespace SteamHeatmap.Web.Tests;

// Golden values mirror analysis/tests/test_scoring.py exactly — this is a
// port of analysis/steamheatmap/scoring.py's wilson_lower_bound and
// concentration_score, and the two must never disagree on the same inputs
// (a game scored on-demand has to land on the same color as one scored by
// the daily pipeline). region_baseline_share is NOT ported: #27 always
// scores against a baseline already persisted by that day's pipeline run
// (#23), never recomputes one.
public class OnDemandScoringTests
{
    [Fact]
    public void ZeroInLanguageReviewsScoresZero()
    {
        var score = OnDemandScoring.WilsonLowerBound(inLanguageReviews: 0, totalReviews: 100);

        Assert.Equal(0.0, score);
    }

    [Fact]
    public void AllReviewsInLanguageScoresNearOne()
    {
        var score = OnDemandScoring.WilsonLowerBound(inLanguageReviews: 100, totalReviews: 100);

        // Hand-computed: for p̂=1, LB = 1/(1+z²/n) = 1/1.0384146 ≈ 0.9630
        Assert.Equal(0.9630, score, precision: 3);
        Assert.True(score < 1.0);
    }

    [Fact]
    public void SmallSampleScoresLowerThanLargeSampleAtSamePercentage()
    {
        // Same raw share (2/3), wildly different sample sizes — ADR-004's core case
        var noisySmall = OnDemandScoring.WilsonLowerBound(inLanguageReviews: 8, totalReviews: 12);
        var solidLarge = OnDemandScoring.WilsonLowerBound(inLanguageReviews: 2000, totalReviews: 3000);

        Assert.True(noisySmall < solidLarge);
    }

    [Fact]
    public void ConcentrationAboveBaselineScoresAboveOne()
    {
        var score = OnDemandScoring.ConcentrationScore(wilsonAdjustedShare: 0.6, baselineShare: 0.4);

        Assert.Equal(1.5, score, precision: 3);
    }

    [Fact]
    public void ConcentrationAtBaselineScoresOne()
    {
        var score = OnDemandScoring.ConcentrationScore(wilsonAdjustedShare: 0.4, baselineShare: 0.4);

        Assert.Equal(1.0, score, precision: 3);
    }
}
