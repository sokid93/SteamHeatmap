import requests

_APPREVIEWS_URL = "https://store.steampowered.com/appreviews/{app_id}"


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
