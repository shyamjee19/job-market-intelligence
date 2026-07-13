from utils.skill_categories import is_ai_skill, is_cloud_skill, is_tech_skill


def test_ai_skill_matches():
    assert is_ai_skill("Machine Learning")
    assert is_ai_skill("GPT")
    assert is_ai_skill("data science")


def test_ai_skill_does_not_false_positive_on_substring():
    # "training" contains "ai" as a bare substring, "teamleitung" contains "ml" -
    # neither is an AI skill, and word-boundary matching must not tag them as one.
    assert not is_ai_skill("training")
    assert not is_ai_skill("teamleitung")


def test_cloud_skill_matches():
    assert is_cloud_skill("AWS")
    assert is_cloud_skill("kubernetes")
    assert not is_cloud_skill("cloudy day")  # sanity: unrelated word shouldn't match differently than expected
    assert is_cloud_skill("cloud")


def test_tech_skill_matches():
    assert is_tech_skill("Python")
    assert is_tech_skill("React")


def test_tech_skill_symbol_keywords():
    assert is_tech_skill("C++ Developer")
    assert is_tech_skill("C#")


def test_tech_skill_short_keyword_does_not_false_positive():
    # "go" must not match inside "google" or "django".
    assert not is_tech_skill("Google Ads")
    assert not is_tech_skill("Django")
    assert is_tech_skill("Go")
