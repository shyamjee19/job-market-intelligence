from utils.geo import infer_country


def test_infers_country_from_explicit_name():
    assert infer_country("São Paulo, São Paulo, Brasil") == "Brazil"


def test_infers_country_from_alias():
    assert infer_country("Ciudad de México") == "Mexico"


def test_infers_country_from_known_city():
    assert infer_country("Berlin") == "Germany"
    assert infer_country("Greater Chicago Area") is None  # not a known exact city segment


def test_infers_country_from_city_in_comma_list():
    assert infer_country("Bangalore, Karnataka, India") == "India"


def test_unknown_location_returns_none():
    assert infer_country("Somewhere Remote") is None


def test_none_and_empty_return_none():
    assert infer_country(None) is None
    assert infer_country("") is None


def test_does_not_false_positive_on_short_alias_inside_another_word():
    # "uk" is a country alias; "Bukavu" merely contains those letters and
    # must not match it - word-boundary matching, not a bare substring scan.
    assert infer_country("Bukavu") is None


def test_known_indian_city_without_country_suffix():
    # Confirms real data we've seen ("Mangaluru," with no country) resolves
    # via the curated city table, not a substring accident.
    assert infer_country("Mangaluru,") == "India"
