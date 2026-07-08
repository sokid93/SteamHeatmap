import pytest

from steamheatmap.scoring import (
    GameLanguageCounts,
    concentration_score,
    region_baseline_share,
    wilson_lower_bound,
)


def test_zero_in_language_reviews_scores_zero():
    score = wilson_lower_bound(in_language_reviews=0, total_reviews=100)

    assert score == 0.0


def test_all_reviews_in_language_scores_near_one():
    score = wilson_lower_bound(in_language_reviews=100, total_reviews=100)

    # Hand-computed: for p̂=1, LB = 1/(1+z²/n) = 1/1.0384146 ≈ 0.9630
    assert score == pytest.approx(0.9630, abs=0.0005)
    assert score < 1.0


def test_small_sample_scores_lower_than_large_sample_at_same_percentage():
    # Same raw share (2/3), wildly different sample sizes — ADR-004's core case
    noisy_small = wilson_lower_bound(in_language_reviews=8, total_reviews=12)
    solid_large = wilson_lower_bound(in_language_reviews=2000, total_reviews=3000)

    assert noisy_small < solid_large


def test_baseline_is_average_of_each_games_raw_share():
    games = [
        GameLanguageCounts(in_language_reviews=50, total_reviews=100),   # share 0.5
        GameLanguageCounts(in_language_reviews=300, total_reviews=1000), # share 0.3
    ]

    baseline = region_baseline_share(games)

    assert baseline == pytest.approx(0.4)  # hand-computed: (0.5 + 0.3) / 2


def test_concentration_above_baseline_scores_above_one():
    score = concentration_score(wilson_adjusted_share=0.6, baseline_share=0.4)

    assert score == pytest.approx(1.5)  # hand-computed: 0.6 / 0.4


def test_concentration_at_baseline_scores_one():
    score = concentration_score(wilson_adjusted_share=0.4, baseline_share=0.4)

    assert score == pytest.approx(1.0)
