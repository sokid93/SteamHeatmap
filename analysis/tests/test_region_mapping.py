from steamheatmap.region_mapping import region_for_language


def test_english_maps_to_a_blended_region():
    region = region_for_language("english")

    assert region.blended is True
    assert region.member_countries == ["US", "UK", "CA", "AU"]
