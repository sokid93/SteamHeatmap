import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from steamheatmap.catalog import CatalogApp

# store.steampowered.com/appreviews was retired in late September 2026 (it
# now redirects to the store homepage). GetItems replaces it: keyless, many
# apps per request, one language per request. Its counts exclude what Steam
# filters out of its review score (e.g. key activations), and it omits a
# language's count below 200 reviews (ADR-013 amendment).
_GETITEMS_URL = "https://api.steampowered.com/IStoreBrowseService/GetItems/v1/"
# Ids travel in the query string; 50 per request keeps the URL short.
_GETITEMS_BATCH_SIZE = 50
_MOST_PLAYED_URL = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
# ISteamApps/GetAppList/v2 (the old, keyless endpoint) no longer exists on
# Steam's live API. IStoreService/GetAppList/v1 is the replacement, requires
# a key, and is paginated (max 50,000 apps/page) rather than single-shot.
_APPLIST_URL = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
_APPLIST_PAGE_SIZE = 50000

# Steam occasionally answers a single call out of the day's few hundred with
# a transient 5xx; without retries that one response kills the whole run.
_RETRIES = Retry(
    total=4,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)


class RequestsSteamClient:
    """Real Steam Web API client. Untested by design (ADR-008) — the seam
    faked in tests is the SteamClient protocol, not this implementation.

    api_key is only required by get_all_apps() (IStoreService/GetAppList,
    ADR-012's one keyed exception). The daily pipeline never passes one —
    GetMostPlayedGames, GetItems and appdetails stay public and keyless."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key
        self._session = requests.Session()
        self._session.mount("https://", HTTPAdapter(max_retries=_RETRIES))

    def _review_summaries(self, app_ids: list[int], language: str) -> dict[int, dict]:
        """GetItems' `reviews` block per app, as seen from `language`."""
        summaries: dict[int, dict] = {}
        for start in range(0, len(app_ids), _GETITEMS_BATCH_SIZE):
            batch = app_ids[start : start + _GETITEMS_BATCH_SIZE]
            request = {
                "ids": [{"appid": app_id} for app_id in batch],
                "context": {"language": language, "country_code": "US"},
                "data_request": {"include_reviews": True},
            }
            response = self._session.get(
                _GETITEMS_URL, params={"input_json": json.dumps(request)}, timeout=30
            )
            response.raise_for_status()
            for item in response.json()["response"]["store_items"]:
                summaries[item["id"]] = item.get("reviews", {})
        return summaries

    def get_total_review_counts(self, app_ids: list[int]) -> dict[int, int]:
        # The total is the same from any language's point of view.
        summaries = self._review_summaries(app_ids, "english")
        # An app Steam returns no reviews block for has no usable reviews.
        return {
            app_id: summaries.get(app_id, {}).get("summary_filtered", {}).get("review_count", 0)
            for app_id in app_ids
        }

    def get_language_review_counts(
        self, app_ids: list[int], language_code: str
    ) -> dict[int, int | None]:
        summaries = self._review_summaries(app_ids, language_code)
        return {
            app_id: summaries.get(app_id, {}).get("summary_language_specific", {}).get("review_count")
            for app_id in app_ids
        }

    def get_most_played_app_ids(self) -> list[int]:
        response = self._session.get(_MOST_PLAYED_URL, timeout=30)
        response.raise_for_status()
        ranks = response.json()["response"]["ranks"]
        return [entry["appid"] for entry in ranks]

    def get_app_name(self, app_id: int) -> str | None:
        response = self._session.get(
            _APPDETAILS_URL,
            params={"appids": app_id, "filters": "basic"},
            timeout=30,
        )
        response.raise_for_status()
        entry = response.json()[str(app_id)]
        if not entry["success"]:
            return None
        return entry["data"]["name"]

    def get_all_apps(self) -> list[CatalogApp]:
        if not self._api_key:
            raise RuntimeError("get_all_apps() requires a Steam API key (STEAM_API_KEY)")

        apps: list[CatalogApp] = []
        last_appid = 0
        while True:
            response = self._session.get(
                _APPLIST_URL,
                params={
                    "key": self._api_key,
                    "max_results": _APPLIST_PAGE_SIZE,
                    "last_appid": last_appid,
                },
                timeout=60,
            )
            response.raise_for_status()
            page = response.json()["response"]
            apps.extend(
                CatalogApp(app_id=entry["appid"], name=entry["name"]) for entry in page["apps"]
            )
            if not page.get("have_more_results"):
                break
            last_appid = page["last_appid"]
        return apps
