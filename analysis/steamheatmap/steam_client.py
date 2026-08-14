import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from steamheatmap.catalog import CatalogApp

_APPREVIEWS_URL = "https://store.steampowered.com/appreviews/{app_id}"
_MOST_PLAYED_URL = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
# ISteamApps/GetAppList/v2 (the old, keyless endpoint) no longer exists on
# Steam's live API. IStoreService/GetAppList/v1 is the replacement, requires
# a key, and is paginated (max 50,000 apps/page) rather than single-shot.
_APPLIST_URL = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
_APPLIST_PAGE_SIZE = 50000

# Steam occasionally answers a single call out of the day's ~3,100 with a
# transient 5xx; without retries that one response kills the whole run.
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
    GetMostPlayedGames and appreviews stay public and keyless."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key
        self._session = requests.Session()
        self._session.mount("https://", HTTPAdapter(max_retries=_RETRIES))

    def _query_summary(self, app_id: int, language: str) -> dict:
        response = self._session.get(
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
