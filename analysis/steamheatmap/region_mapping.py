from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    code: str
    display_name: str
    member_countries: list[str]
    blended: bool


_LANGUAGE_TO_REGION: dict[str, Region] = {
    "english": Region(
        code="english",
        display_name="English-speaking",
        member_countries=["US", "UK", "CA", "AU"],
        blended=True,
    ),
}


def region_for_language(language_code: str) -> Region:
    return _LANGUAGE_TO_REGION[language_code]
