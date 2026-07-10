import pytest

from steamheatmap.pipeline import TrackedGame, fetch_tracked_games, run_pipeline


class FakeSteamClient:
    """Canned responses standing in for the real Steam Web API."""

    def __init__(
        self,
        counts: dict[tuple[int, str], int] | None = None,
        totals: dict[int, int] | None = None,
        most_played: list[int] | None = None,
        names: dict[int, str] | None = None,
    ):
        self._counts = counts or {}
        self._totals = totals or {}
        self._most_played = most_played or []
        self._names = names or {}

    def get_total_review_count(self, app_id: int) -> int:
        return self._totals[app_id]

    def get_language_review_count(self, app_id: int, language_code: str) -> int:
        return self._counts[(app_id, language_code)]

    def get_most_played_app_ids(self) -> list[int]:
        return self._most_played

    def get_app_name(self, app_id: int) -> str | None:
        return self._names.get(app_id)


class FakeWriter:
    def __init__(self):
        self.written_rows = []

    def write_region_scores(self, rows) -> None:
        self.written_rows.extend(rows)


def test_fetch_tracked_games_returns_app_id_and_name_from_steam():
    steam = FakeSteamClient(most_played=[730], names={730: "Counter-Strike 2"})

    tracked = fetch_tracked_games(steam, limit=1)

    assert tracked == [TrackedGame(app_id=730, name="Counter-Strike 2")]


def test_fetch_tracked_games_keeps_only_the_top_limit_games():
    steam = FakeSteamClient(
        most_played=[730, 570, 578080],
        names={730: "Counter-Strike 2", 570: "Dota 2", 578080: "PUBG"},
    )

    tracked = fetch_tracked_games(steam, limit=2)

    assert [game.app_id for game in tracked] == [730, 570]


def test_fetch_tracked_games_skips_games_with_no_available_name():
    # appdetails can fail for delisted/region-locked apps; those games are dropped
    steam = FakeSteamClient(most_played=[730, 999999], names={730: "Counter-Strike 2"})

    tracked = fetch_tracked_games(steam, limit=2)

    assert tracked == [TrackedGame(app_id=730, name="Counter-Strike 2")]


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


def test_pipeline_writes_no_rows_for_a_game_with_zero_total_reviews():
    # Seen in production: an unreleased/review-disabled game in the top 100.
    # No reviews means no language signal, so the game is left unscored.
    steam = FakeSteamClient(
        totals={730: 100, 111: 0},
        counts={(730, "english"): 50, (111, "english"): 0},
    )
    writer = FakeWriter()

    run_pipeline(steam, writer, app_ids=[730, 111], language_codes=["english"])

    assert [row.app_id for row in writer.written_rows] == [730]


def test_pipeline_baseline_ignores_zero_review_games():
    # If the zero-review game wrongly counted as a 0% share, the baseline
    # would halve to 0.25 and 730's concentration would inflate to ≈1.62.
    steam = FakeSteamClient(
        totals={730: 100, 111: 0},
        counts={(730, "english"): 50, (111, "english"): 0},
    )
    writer = FakeWriter()

    run_pipeline(steam, writer, app_ids=[730, 111], language_codes=["english"])

    row_730 = next(row for row in writer.written_rows if row.app_id == 730)
    # Hand-computed: Wilson LB(50/100) ≈ 0.4038, baseline from 730 alone = 0.5
    assert row_730.concentration == pytest.approx(0.4038 / 0.5, abs=0.005)


def test_pipeline_baseline_spans_all_tracked_games():
    # 730 has 50% english share, 570 has 10% — baseline is their average, 0.3.
    # If the baseline wrongly used only 730's own share (0.5), its
    # concentration would be ≈0.81 instead of the expected ≈1.35.
    steam = FakeSteamClient(
        totals={730: 100, 570: 100},
        counts={(730, "english"): 50, (570, "english"): 10},
    )
    writer = FakeWriter()

    run_pipeline(steam, writer, app_ids=[730, 570], language_codes=["english"])

    row_730 = next(row for row in writer.written_rows if row.app_id == 730)
    # Hand-computed: Wilson LB(50/100) ≈ 0.4038, baseline (0.5 + 0.1) / 2 = 0.3
    assert row_730.concentration == pytest.approx(0.4038 / 0.3, abs=0.005)
