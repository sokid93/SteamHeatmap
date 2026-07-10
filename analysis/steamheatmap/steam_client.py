import requests

_APPREVIEWS_URL = "https://store.steampowered.com/appreviews/{app_id}"
_MOST_PLAYED_URL = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"


class RequestsSteamClient:
    """Real Steam Web API client. Untested by design (ADR-008) — the seam
    faked in tests is the SteamClient protocol, not this implementation."""

    def _query_summary(self, app_id: int, language: str) -> dict:
        response = requests.get(
            _APPREVIEWS_URL.format(app_id=app_id),
            params={"json": 1, "language": language, "num_per_page": 0, "purchase_type": "all"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["query_summary"]

    def get_total_review_count(self, app_id: int) -> int:
        return self._query_summary(app_id, "all")["total_reviews"]

    def get_language_review_count(self, app_id: int, language_code: str) -> int:
        return self._query_summary(app_id, language_code)["total_reviews"]

    def get_most_played_app_ids(self) -> list[int]:
        response = requests.get(_MOST_PLAYED_URL, timeout=30)
        response.raise_for_status()
        ranks = response.json()["response"]["ranks"]
        return [entry["appid"] for entry in ranks]

    def get_app_name(self, app_id: int) -> str | None:
        response = requests.get(
            _APPDETAILS_URL,
            params={"appids": app_id, "filters": "basic"},
            timeout=30,
        )
        response.raise_for_status()
        entry = response.json()[str(app_id)]
        if not entry["success"]:
            return None
        return entry["data"]["name"]
