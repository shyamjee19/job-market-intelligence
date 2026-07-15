from ai.services import rate_limiter
from config.settings import settings


def test_allows_requests_up_to_the_limit():
    client_id = "test-client-allow"
    for _ in range(settings.AI_RATE_LIMIT_PER_MINUTE):
        assert rate_limiter.check_rate_limit(client_id) is True


def test_blocks_requests_over_the_limit():
    client_id = "test-client-block"
    for _ in range(settings.AI_RATE_LIMIT_PER_MINUTE):
        rate_limiter.check_rate_limit(client_id)
    assert rate_limiter.check_rate_limit(client_id) is False


def test_different_clients_have_independent_limits():
    for _ in range(settings.AI_RATE_LIMIT_PER_MINUTE):
        rate_limiter.check_rate_limit("client-a")
    assert rate_limiter.check_rate_limit("client-a") is False
    assert rate_limiter.check_rate_limit("client-b") is True
