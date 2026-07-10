import pytest

from steamheatmap.region_mapping import region_for_language, supported_language_codes

# Expected pairs come from ADR-002's "Concrete mapping" table.
SINGLE_COUNTRY_LANGUAGES = [
    ("schinese", "CN"),
    ("brazilian", "BR"),
    ("spanish", "ES"),
    ("italian", "IT"),
    ("japanese", "JP"),
    ("koreana", "KR"),
    ("polish", "PL"),
    ("turkish", "TR"),
    ("ukrainian", "UA"),
    ("czech", "CZ"),
    ("hungarian", "HU"),
    ("bulgarian", "BG"),
    ("danish", "DK"),
    ("finnish", "FI"),
    ("norwegian", "NO"),
    ("swedish", "SE"),
    ("thai", "TH"),
    ("vietnamese", "VN"),
    ("indonesian", "ID"),
]


@pytest.mark.parametrize("language_code,country", SINGLE_COUNTRY_LANGUAGES)
def test_single_country_language_maps_to_its_country(language_code, country):
    region = region_for_language(language_code)

    assert region.member_countries == [country]
    assert region.blended is False


# Expected lists come from ADR-002's "Concrete mapping" table.
BLENDED_REGION_MEMBERS = [
    ("english", ["US", "GB", "IE", "CA", "AU", "NZ", "IN", "PK", "BD", "PH",
                 "SG", "MY", "ZA", "NG", "KE", "GH"]),
    ("latam", ["MX", "AR", "CO", "CL", "PE", "VE", "EC", "GT", "BO", "DO",
               "HN", "PY", "SV", "NI", "CR", "PA", "UY", "CU"]),
    ("arabic", ["SA", "AE", "EG", "IQ", "JO", "KW", "QA", "BH", "OM", "LB",
                "SY", "YE", "LY", "SD", "DZ", "MA", "TN"]),
    ("russian", ["RU", "BY", "KZ", "KG", "UZ", "TJ", "TM", "AM", "AZ"]),
    ("french", ["FR", "LU", "SN", "CI", "CM", "CD", "ML", "BF", "NE", "TG",
                "BJ", "GA", "CG", "HT"]),
    ("german", ["DE", "AT", "CH"]),
    ("dutch", ["NL", "BE"]),
    ("tchinese", ["TW", "HK", "MO"]),
    ("portuguese", ["PT", "AO", "MZ"]),
    ("greek", ["GR", "CY"]),
    ("romanian", ["RO", "MD"]),
]


@pytest.mark.parametrize("language_code,members", BLENDED_REGION_MEMBERS)
def test_blended_language_maps_to_its_member_countries(language_code, members):
    region = region_for_language(language_code)

    assert region.member_countries == members
    assert region.blended is True


def test_all_thirty_steam_review_languages_are_supported():
    # Steam's documented review language codes (store API language list).
    expected = {
        "arabic", "bulgarian", "schinese", "tchinese", "czech", "danish",
        "dutch", "english", "finnish", "french", "german", "greek",
        "hungarian", "indonesian", "italian", "japanese", "koreana",
        "norwegian", "polish", "portuguese", "brazilian", "romanian",
        "russian", "spanish", "latam", "swedish", "thai", "turkish",
        "ukrainian", "vietnamese",
    }

    assert set(supported_language_codes()) == expected
