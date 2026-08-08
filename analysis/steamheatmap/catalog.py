from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CatalogApp:
    app_id: int
    name: str


class CatalogSteamClient(Protocol):
    def get_all_apps(self) -> list[CatalogApp]: ...


class CatalogWriter(Protocol):
    def write_catalog(self, apps: list[CatalogApp]) -> None: ...


def refresh_catalog(steam: CatalogSteamClient, writer: CatalogWriter) -> int:
    apps = steam.get_all_apps()
    writer.write_catalog(apps)
    return len(apps)
