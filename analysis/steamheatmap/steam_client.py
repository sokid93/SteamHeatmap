import json
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from steamheatmap.catalog import CatalogApp

# Valve's documented replacement for the retired store.steampowered.com/
# appreviews: keyless, one app and one language per call, same counts.
_APP_REVIEWS_URL = "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/"
# Enum values: purchase_type 1 = all purchases (appreviews' purchase_type=all,
# so key activations count); review_type 0 = all, the only value for which
# query_summary carries total_reviews.
_PURCHASE_TYPE_ALL = 1
_REVIEW_TYPE_ALL = 0
_MOST_PLAYED_URL = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
# ISteamApps/GetAppList/v2 (the old, keyless endpoint) no longer exists on
# Steam's live API. IStoreService/GetAppList/v1 is the replacement, requires
# a key, and is paginated (max 50,000 apps/page) rather than single-shot.
_APPLIST_URL = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
_APPLIST_PAGE_SIZE = 50000

# Steam occasionally answers a single call out of the day's ~4,250 with a
# transient 5xx (or a 429: keyless GetAppReviews calls share a lower rate
# limit); without retries that one response kills the whole run.
_RETRIES = Retry(
    total=4,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)


class UnexpectedSteamResponse(RuntimeError):
    """Steam answered successfully but not with JSON: the endpoint has most
    likely been changed or retired."""

    def __init__(self, url: str, response: requests.Response, content_type: str) -> None:
        # Never echo response.url: it carries the query string, API key included.
        final = urlsplit(response.url)
        redirect = (
            f", after a redirect to {final.scheme}://{final.netloc}{final.path}"
            if response.history
            else ""
        )
        super().__init__(
            f"{url} answered {response.status_code} with {content_type or 'no content type'}"
            f"{redirect} instead of JSON. Steam may have changed or retired this endpoint."
        )


class RequestsSteamClient:
    """Real Steam Web API client. Untested by design (ADR-008) — the seam
    faked in tests is the SteamClient protocol, not this implementation.

    api_key is only required by get_all_apps() (IStoreService/GetAppList,
    ADR-012's one keyed exception). The daily pipeline never passes one —
    GetMostPlayedGames, GetAppReviews and appdetails stay public and keyless."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key
        self._session = requests.Session()
        self._session.mount("https://", HTTPAdapter(max_retries=_RETRIES))

    def _get_json(self, url: str, params: dict | None = None, timeout: int = 30):
        response = self._session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        # A retired endpoint can still answer 200 — appreviews redirects to the
        # store's HTML homepage — so a successful status alone proves nothing.
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type:
            raise UnexpectedSteamResponse(url, response, content_type)
        return response.json()

    def _review_count(self, app_id: int, language: str) -> int:
        request = {
            "appid": app_id,
            "languages": [language],
            # Only the count is needed, but 0 means "default" (20 full reviews).
            "num_per_page": 1,
            "purchase_type": _PURCHASE_TYPE_ALL,
            "review_type": _REVIEW_TYPE_ALL,
        }
        page = self._get_json(_APP_REVIEWS_URL, params={"input_json": json.dumps(request)})
        # Some apps (e.g. ones without a public store page) get an empty
        # response: no usable reviews.
        summary = page["response"].get("query_summary", {})
        return summary.get("total_reviews", 0)

    def get_total_review_counts(self, app_ids: list[int]) -> dict[int, int]:
        return {app_id: self._review_count(app_id, "all") for app_id in app_ids}

    def get_language_review_counts(
        self, app_ids: list[int], language_code: str
    ) -> dict[int, int]:
        return {app_id: self._review_count(app_id, language_code) for app_id in app_ids}

    def get_most_played_app_ids(self) -> list[int]:
        ranks = self._get_json(_MOST_PLAYED_URL)["response"]["ranks"]
        return [entry["appid"] for entry in ranks]

    def get_app_name(self, app_id: int) -> str | None:
        details = self._get_json(_APPDETAILS_URL, params={"appids": app_id, "filters": "basic"})
        entry = details[str(app_id)]
        if not entry["success"]:
            return None
        return entry["data"]["name"]

    def get_all_apps(self) -> list[CatalogApp]:
        if not self._api_key:
            raise RuntimeError("get_all_apps() requires a Steam API key (STEAM_API_KEY)")

        apps: list[CatalogApp] = []
        last_appid = 0
        while True:
            page = self._get_json(
                _APPLIST_URL,
                params={
                    "key": self._api_key,
                    "max_results": _APPLIST_PAGE_SIZE,
                    "last_appid": last_appid,
                },
                timeout=60,
            )["response"]
            apps.extend(
                CatalogApp(app_id=entry["appid"], name=entry["name"]) for entry in page["apps"]
            )
            if not page.get("have_more_results"):
                break
            last_appid = page["last_appid"]
        return apps
