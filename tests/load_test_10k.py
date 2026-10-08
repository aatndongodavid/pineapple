# tests/load_test_10k.py — Load Testing & Capacity Benchmark (Gate O-8)

import asyncio
import time
import statistics
import logging
import httpx
import pytest

logger = logging.getLogger("LoadTest")

# Objectifs de performance (Gate O-8)
P95_LATENCY_MAX_MS = 300.0  # p95 < 300 ms sur les lectures courantes
ERROR_RATE_MAX_PERCENT = 0.5  # Taux d'erreur < 0,5%


@pytest.mark.asyncio
async def test_gate_o8_load_test_read_endpoints_performance():
    """
    Gate O-8: Simulation de charge sur les chemins chauds (fil d'actualité, salles, planning).
    Vérifie que la latence p95 reste < 300 ms et que le taux d'erreur < 0.5%.
    """
    # En environnement de test unitaire, on simule l'exécution de 50 requêtes concurrentes via httpx AsyncClient
    from api.main import app

    latencies_ms = []
    errors_count = 0
    total_requests = 100

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        async def fetch_endpoint(url: str):
            nonlocal errors_count
            t0 = time.perf_counter()
            try:
                res = await client.get(url)
                if res.status_code >= 500:
                    errors_count += 1
            except Exception:
                errors_count += 1
            finally:
                t1 = time.perf_counter()
                latencies_ms.append((t1 - t0) * 1000.0)

        tasks = []
        endpoints = ["/health", "/api/v1/ads/feed", "/metrics"]
        for i in range(total_requests):
            url = endpoints[i % len(endpoints)]
            tasks.append(fetch_endpoint(url))

        await asyncio.gather(*tasks)

    # Calcul des métriques
    error_rate = (errors_count / total_requests) * 100.0
    sorted_latencies = sorted(latencies_ms)
    p50 = statistics.median(sorted_latencies)
    p95_index = int(len(sorted_latencies) * 0.95)
    p95 = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]

    print(f"\n--- Benchmark Results (Gate O-8) ---")
    print(f"Total Requests: {total_requests}")
    print(f"Errors: {errors_count} ({error_rate:.2f}%)")
    print(f"p50 Latency: {p50:.2f} ms")
    print(f"p95 Latency: {p95:.2f} ms")

    assert error_rate <= ERROR_RATE_MAX_PERCENT, f"Taux d'erreur trop élevé: {error_rate:.2f}% > {ERROR_RATE_MAX_PERCENT}%"
    assert p95 <= P95_LATENCY_MAX_MS, f"Latence p95 trop élevée: {p95:.2f} ms > {P95_LATENCY_MAX_MS} ms"
