# tests/unit/test_observability_and_redis_degradation.py

from unittest.mock import patch, AsyncMock
import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError

from shared_kernel.config import settings
from shared_kernel.infrastructure.rate_limiter import rate_limit_sensitive_endpoint
from shared_kernel.infrastructure.metrics import get_prometheus_metrics_response


@pytest.mark.asyncio
async def test_gate_o4_redis_failure_fails_closed_in_production():
    """
    Gate O-4: En cas de coupure de Redis en production, le rate limiter échoue de manière fermée (Fail-Closed, HTTP 503).
    """
    mock_request = AsyncMock()
    mock_request.client.host = "192.168.1.50"
    mock_request.url.path = "/api/v1/identity/login"

    dep = rate_limit_sensitive_endpoint(max_requests=5, window_seconds=60)

    # Simuler l'environnement de production et la panne de Redis
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch("shared_kernel.infrastructure.rate_limiter.get_redis_client", side_effect=RedisError("Connection refused")):
            with pytest.raises(HTTPException) as exc_info:
                await dep(mock_request)

            assert exc_info.value.status_code == 503
            assert exc_info.value.detail["code"] == "REDIS_UNAVAILABLE_FAIL_CLOSED"


def test_gate_o5_prometheus_metrics_endpoint_returns_data():
    """
    Gate O-5: L'endpoint /metrics renvoie un contenu au format texte Prometheus valide.
    """
    response = get_prometheus_metrics_response()
    assert response.status_code == 200
    assert "text/plain" in response.media_type or "version=0.0.4" in response.media_type
    content = response.body.decode("utf-8")
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
