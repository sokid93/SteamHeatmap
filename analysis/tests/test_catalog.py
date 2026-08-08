from steamheatmap.catalog import CatalogApp, refresh_catalog


class FakeCatalogSteamClient:
    def __init__(self, apps: list[CatalogApp] | None = None):
        self._apps = apps or []

    def get_all_apps(self) -> list[CatalogApp]:
        return self._apps


class FakeCatalogWriter:
    def __init__(self):
        self.written_apps = []

    def write_catalog(self, apps: list[CatalogApp]) -> None:
        self.written_apps.extend(apps)


def test_refresh_catalog_writes_every_app_from_steam():
    steam = FakeCatalogSteamClient(
        apps=[CatalogApp(app_id=730, name="Counter-Strike 2"), CatalogApp(app_id=570, name="Dota 2")]
    )
    writer = FakeCatalogWriter()

    refresh_catalog(steam, writer)

    assert writer.written_apps == [
        CatalogApp(app_id=730, name="Counter-Strike 2"),
        CatalogApp(app_id=570, name="Dota 2"),
    ]
