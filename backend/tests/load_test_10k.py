# backend/tests/load_test_10k.py

import asyncio
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"
TOTAL_REQUESTS = 1000
CONCURRENCY = 50

async def worker(client: httpx.AsyncClient, queue: asyncio.Queue, results: list):
    while not queue.empty():
        req_id = await queue.get()
        start = time.perf_counter()
        try:
            res = await client.get(f"{BASE_URL}/health")
            elapsed = (time.perf_counter() - start) * 1000.0  # ms
            results.append((res.status_code, elapsed))
        except Exception as err:
            results.append((500, 0.0))
        finally:
            queue.task_done()

async def main():
    print(f"=== Pineapple Benchmark: {TOTAL_REQUESTS} requests with concurrency {CONCURRENCY} ===")
    queue = asyncio.Queue()
    for i in range(TOTAL_REQUESTS):
        queue.put_nowait(i)

    results = []
    start_total = time.perf_counter()

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [asyncio.create_task(worker(client, queue, results)) for _ in range(CONCURRENCY)]
        await queue.join()
        for t in tasks:
            t.cancel()

    total_time = time.perf_counter() - start_total
    successes = [r for r in results if r[0] == 200]
    latencies = [r[1] for r in successes]

    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
    p95_lat = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0
    rps = len(results) / total_time

    print(f"Total time: {total_time:.2f} s")
    print(f"Throughput: {rps:.2f} req/s")
    print(f"Success rate: {len(successes)}/{TOTAL_REQUESTS} ({len(successes)/TOTAL_REQUESTS*100:.1f}%)")
    print(f"Avg latency: {avg_lat:.2f} ms")
    print(f"P95 latency: {p95_lat:.2f} ms")

if __name__ == "__main__":
    asyncio.run(main())
