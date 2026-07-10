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
