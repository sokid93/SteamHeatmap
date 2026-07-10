from dataclasses import dataclass
from typing import Protocol

from steamheatmap.region_mapping import region_for_language
from steamheatmap.scoring import (
    GameLanguageCounts,
    concentration_score,
    region_baseline_share,
    wilson_lower_bound,
)


class SteamClient(Protocol):
    def get_total_review_count(self, app_id: int) -> int: ...

    def get_language_review_count(self, app_id: int, language_code: str) -> int: ...

    def get_most_played_app_ids(self) -> list[int]: ...

    def get_app_name(self, app_id: int) -> str | None: ...


@dataclass(frozen=True)
class TrackedGame:
    app_id: int
    name: str


def fetch_tracked_games(steam: SteamClient, limit: int) -> list[TrackedGame]:
    tracked: list[TrackedGame] = []
    for app_id in steam.get_most_played_app_ids()[:limit]:
        name = steam.get_app_name(app_id)
        if name is None:
            continue
        tracked.append(TrackedGame(app_id=app_id, name=name))
    return tracked


@dataclass(frozen=True)
class RegionGameScore:
    app_id: int
    region_code: str
    total_reviews: int
    in_language_reviews: int
    wilson_adjusted_share: float
    concentration: float


class RegionScoreWriter(Protocol):
    def write_region_scores(self, rows: list[RegionGameScore]) -> None: ...


def run_pipeline(
    steam: SteamClient,
    writer: RegionScoreWriter,
    app_ids: list[int],
    language_codes: list[str],
) -> None:
    totals = {app_id: steam.get_total_review_count(app_id) for app_id in app_ids}

    # A game with zero reviews carries no language signal (its share would be
    # 0/0), so it is left out of both scoring and the baseline.
    reviewed_app_ids = [app_id for app_id in app_ids if totals[app_id] > 0]

    counts = {
        (app_id, lang): steam.get_language_review_count(app_id, lang)
        for app_id in reviewed_app_ids
        for lang in language_codes
    }

    rows: list[RegionGameScore] = []
    for lang in language_codes:
        region = region_for_language(lang)
        tracked = [
            GameLanguageCounts(
                in_language_reviews=counts[(app_id, lang)],
                total_reviews=totals[app_id],
            )
            for app_id in reviewed_app_ids
        ]
        baseline = region_baseline_share(tracked)

        for app_id in reviewed_app_ids:
            adjusted = wilson_lower_bound(
                in_language_reviews=counts[(app_id, lang)],
                total_reviews=totals[app_id],
            )
            rows.append(
                RegionGameScore(
                    app_id=app_id,
                    region_code=region.code,
                    total_reviews=totals[app_id],
                    in_language_reviews=counts[(app_id, lang)],
                    wilson_adjusted_share=adjusted,
                    concentration=concentration_score(adjusted, baseline),
                )
            )

    writer.write_region_scores(rows)
