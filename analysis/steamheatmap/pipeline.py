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
    counts = {
        (app_id, lang): steam.get_language_review_count(app_id, lang)
        for app_id in app_ids
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
            for app_id in app_ids
        ]
        baseline = region_baseline_share(tracked)

        for app_id in app_ids:
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
