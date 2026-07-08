import pytest

from steamheatmap.pipeline import run_pipeline


class FakeSteamClient:
    """Canned counts standing in for real appreviews responses."""

    def __init__(self, counts: dict[tuple[int, str], int], totals: dict[int, int]):
        self._counts = counts
        self._totals = totals

    def get_total_review_count(self, app_id: int) -> int:
        return self._totals[app_id]

    def get_language_review_count(self, app_id: int, language_code: str) -> int:
        return self._counts[(app_id, language_code)]


class FakeWriter:
    def __init__(self):
        self.written_rows = []

    def write_region_scores(self, rows) -> None:
        self.written_rows.extend(rows)


def test_pipeline_scores_one_game_one_language_and_writes_result():
    steam = FakeSteamClient(totals={730: 100}, counts={(730, "english"): 50})
    writer = FakeWriter()

    run_pipeline(steam, writer, app_ids=[730], language_codes=["english"])

    assert len(writer.written_rows) == 1
    row = writer.written_rows[0]
    assert row.app_id == 730
    assert row.region_code == "english"
    assert row.total_reviews == 100
    assert row.in_language_reviews == 50
    # Wilson LB for 50/100 at 95% ≈ 0.4038 (standard reference value)
    assert row.wilson_adjusted_share == pytest.approx(0.4038, abs=0.0005)
    # Baseline across the (single-game) tracked set is 0.5; 0.4038 / 0.5
    assert row.concentration == pytest.approx(0.8077, abs=0.001)
