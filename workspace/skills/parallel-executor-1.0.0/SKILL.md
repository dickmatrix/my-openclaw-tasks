---
name: Parallel Executor
description: Executes multiple independent sub-tasks concurrently using Python ThreadPoolExecutor or asyncio, converting serial wait time into parallel processing. Use when the user has multiple independent operations (API calls, file processing, downloads) that can run simultaneously to save time.
read_when:
  - Running multiple API calls simultaneously
  - Processing N files independently in parallel
  - Downloading multiple URLs concurrently
  - Converting serial task queues to concurrent execution
metadata: {"clawdbot":{"emoji":"⚡"}}
---

# Parallel Executor Skill

Converts serial task queues into concurrent execution. Key rule: **only parallelize truly independent tasks** (no shared mutable state, no order dependency).

## When to use

- Multiple API calls to different endpoints
- Processing N files independently
- Downloading multiple URLs
- Running independent data transformations

## Pattern 1: ThreadPoolExecutor (I/O-bound, simplest)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_one(item):
    return {"item": item, "result": item * 2}  # replace with real task

def run_parallel(items: list, max_workers: int = 8):
    results, errors = [], []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                results.append(future.result())
            except Exception as e:
                errors.append({"item": item, "error": str(e)})
    return results, errors

results, errors = run_parallel([1, 2, 3, 4, 5])
print(f"Done: {len(results)} ok, {len(errors)} failed")
```

## Pattern 2: asyncio + httpx (async API calls)

```python
import asyncio, httpx

async def fetch_one(client: httpx.AsyncClient, url: str) -> dict:
    r = await client.get(url, timeout=10)
    return {"url": url, "status": r.status_code, "size": len(r.content)}

async def fetch_all(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[fetch_one(client, url) for url in urls],
            return_exceptions=True
        )
    return [
        r if not isinstance(r, Exception) else {"url": urls[i], "error": str(r)}
        for i, r in enumerate(results)
    ]

results = asyncio.run(fetch_all(["https://api1.com", "https://api2.com"]))
```

## Pattern 3: ProcessPoolExecutor (CPU-bound)

```python
from concurrent.futures import ProcessPoolExecutor

def cpu_heavy(data: list) -> int:
    return sum(x**2 for x in data)

def run_cpu_parallel(chunks: list[list]) -> list[int]:
    with ProcessPoolExecutor() as executor:
        return list(executor.map(cpu_heavy, chunks))
```

## Chunking helper

```python
def chunk(lst: list, size: int) -> list[list]:
    return [lst[i:i+size] for i in range(0, len(lst), size)]

# 1000 items, batches of 50, 10 workers
batches = chunk(items, 50)
results, errors = run_parallel(batches, max_workers=10)
```

## Rate limiting

```python
import time
from threading import Semaphore

RATE_LIMIT = Semaphore(5)  # max 5 concurrent

def rate_limited_call(url: str) -> 