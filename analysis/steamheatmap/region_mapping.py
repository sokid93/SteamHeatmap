from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    code: str
    display_name: str
    member_countries: list[str]
    blended: bool


# (display name, member countries as ISO 3166-1 alpha-2) per language code.
# Membership follows ADR-002's "Concrete mapping": native language when Steam
# supports it, otherwise the language the country's Steam users review in.
_REGION_DATA: dict[str, tuple[str, list[str]]] = {
    "english": ("English-speaking", ["US", "GB", "IE", "CA", "AU", "NZ", "IN",
                                     "PK", "BD", "PH", "SG", "MY", "ZA", "NG",
                                     "KE", "GH"]),
    "latam": ("Latin America", ["MX", "AR", "CO", "CL", "PE", "VE", "EC",
                                "GT", "BO", "DO", "HN", "PY", "SV", "NI",
                                "CR", "PA", "UY", "CU"]),
    "arabic": ("Arabic-speaking", ["SA", "AE", "EG", "IQ", "JO", "KW", "QA",
                                   "BH", "OM", "LB", "SY", "YE", "LY", "SD",
                                   "DZ", "MA", "TN"]),
    "russian": ("Russian-speaking", ["RU", "BY", "KZ", "KG", "UZ", "TJ", "TM",
                                     "AM", "AZ"]),
    "french": ("French-speaking", ["FR", "LU", "SN", "CI", "CM", "CD", "ML",
                                   "BF", "NE", "TG", "BJ", "GA", "CG", "HT"]),
    "german": ("German-speaking", ["DE", "AT", "CH"]),
    "dutch": ("Dutch-speaking", ["NL", "BE"]),
    "tchinese": ("Traditional Chinese (Taiwan, Hong Kong & Macau)", ["TW", "HK", "MO"]),
    "portuguese": ("Portuguese-speaking (Portugal & Africa)", ["PT", "AO", "MZ"]),
    "greek": ("Greece & Cyprus", ["GR", "CY"]),
    "romanian": ("Romania & Moldova", ["RO", "MD"]),
    "schinese": ("China (Simplified Chinese)", ["CN"]),
    "brazilian": ("Brazil", ["BR"]),
    "spanish": ("Spain", ["ES"]),
    "italian": ("Italy", ["IT"]),
    "japanese": ("Japan", ["JP"]),
    "koreana": ("South Korea", ["KR"]),
    "polish": ("Poland", ["PL"]),
    "turkish": ("Turkey", ["TR"]),
    "ukrainian": ("Ukraine", ["UA"]),
    "czech": ("Czechia", ["CZ"]),
    "hungarian": ("Hungary", ["HU"]),
    "bulgarian": ("Bulgaria", ["BG"]),
    "danish": ("Denmark", ["DK"]),
    "finnish": ("Finland", ["FI"]),
    "norwegian": ("Norway", ["NO"]),
    "swedish": ("Sweden", ["SE"]),
    "thai": ("Thailand", ["TH"]),
    "vietnamese": ("Vietnam", ["VN"]),
    "indonesian": ("Indonesia", ["ID"]),
}

_LANGUAGE_TO_REGION: dict[str, Region] = {
    code: Region(
        code=code,
        display_name=display_name,
        member_countries=member_countries,
        blended=len(member_countries) > 1,
    )
    for code, (display_name, member_countries) in _REGION_DATA.items()
}


def region_for_language(language_code: str) -> Region:
    return _LANGUAGE_TO_REGION[language_code]
