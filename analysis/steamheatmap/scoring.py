import math
from dataclasses import dataclass

_Z_95 = 1.959963985


@dataclass(frozen=True)
class GameLanguageCounts:
    in_language_reviews: int
    total_reviews: int


def wilson_lower_bound(
    in_language_reviews: int, total_reviews: int, confidence_z: float = _Z_95
) -> float:
    n = total_reviews
    p_hat = in_language_reviews / n
    z = confidence_z

    denominator = 1 + z * z / n
    center = p_hat + z * z / (2 * n)
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z * z / (4 * n)) / n)

    return (center - margin) / denominator


def region_baseline_share(games: list[GameLanguageCounts]) -> float:
    shares = [g.in_language_reviews / g.total_reviews for g in games]
    return sum(shares) / len(shares)


def concentration_score(wilson_adjusted_share: float, baseline_share: float) -> float:
    return wilson_adjusted_share / baseline_share
