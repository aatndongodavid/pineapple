# backend/src/shared_kernel/infrastructure/metrics.py

import time
import logging
from typing import Callable
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger("MetricsService")

# Métriques Prometheus (Ne sont plus un placeholder!)
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Nombre total de requêtes HTTP traitées par Pineapple OS",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Durée de traitement des requêtes HTTP en secondes",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

ACTIVE_WEBSOCKET_CONNECTIONS = Gauge(
    "active_websocket_connections",
    "Nombre de connexions WebSocket actuellement actives",
)

DB_POOL_ACTIVE_CONNECTIONS = Gauge(
    "db_pool_active_connections",
    "Nombre de connexions actives dans le pool SQLAlchemy",
)

REDIS_AVAILABLE = Gauge(
    "redis_available",
    "Disponibilité du cluster Redis (1 = UP, 0 = DOWN)",
)


async def prometheus_metrics_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware d'interception et de mesure de la latence p50/p95/p99 pour Prometheus.
    """
    start_time = time.time()
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status_code = str(response.status_code)
    except Exception as exc:
        status_code = "500"
        raise exc from None
    finally:
        duration = time.time() - start_time
        # Normaliser l'endpoint pour éviter l'explosion de cardinalité
        normalized_endpoint = endpoint if len(endpoint) < 50 else "/".join(endpoint.split("/")[:4])
        HTTP_REQUESTS_TOTAL.labels(method=request.method, endpoint=normalized_endpoint, status_code=status_code).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, endpoint=normalized_endpoint).observe(duration)

    return response


def get_prometheus_metrics_response() -> Response:
    """
    Génère la réponse contenant le format texte standard Prometheus.
    """
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
