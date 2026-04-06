---
name: Platform API Bridge
description: Integrates with freelance platform APIs (Upwork, Fiverr) and social media APIs (Twitter/X, LinkedIn, Reddit) using direct HTTP calls instead of UI simulation. Use when the user needs to fetch jobs, post listings, read notifications, send messages, or interact with any platform API programmatically.
read_when:
  - Fetching jobs or listings from Upwork or Fiverr
  - Searching or posting to Twitter/X, Reddit, or LinkedIn
  - Making authenticated REST API calls to any platform
  - Replacing UI automation with direct API calls
metadata: {"clawdbot":{"emoji":"🔌"}}
---

# Platform API Bridge Skill

Direct API calls replace fragile UI automation — millisecond latency, near-zero failure rate.

## Setup

```bash
pip install httpx python-dotenv
```

Store credentials in `.env`:
```
UPWORK_CLIENT_ID=xxx
UPWORK_CLIENT_SECRET=xxx
TWITTER_BEARER_TOKEN=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_SECRET=xxx
```

```python
from dotenv import load_dotenv
import os
load_dotenv()
```

## Generic REST client

```python
import httpx

class APIClient:
    def __init__(self, base_url: str, headers: dict):
        self.base = base_url
        self.headers = headers

    def get(self, path: str, params: dict = None) -> dict:
        r = httpx.get(f"{self.base}{path}", headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, body: dict) -> dict:
        r = httpx.post(f"{self.base}{path}", headers=self.headers, json=body)
        r.raise_for_status()
        return r.json()
```

## Upwork

```python
import httpx, os

def get_upwork_token() -> str:
    r = httpx.post(
        "https://www.upwork.com/api/v3/oauth2/token",
        data={"grant_type": "client_credentials",
              "client_id": os.getenv("UPWORK_CLIENT_ID"),
              "client_secret": os.getenv("UPWORK_CLIENT_SECRET")}
    )
    return r.json()["access_token"]

def search_jobs(query: str, limit: int = 10) -> list[dict]:
    token = get_upwork_token()
    client = APIClient("https://www.upwork.com/api/profiles/v2",
                       {"Authorization": f"Bearer {token}"})
    data = client.get("/search/jobs/v2", {"q": query, "paging": f"0;{limit}"})
    return [{"title": j["title"], "budget": j.get("budget"), "url": j["url"]}
            for j in data.get("jobs", {}).get("job", [])]
```

## Twitter / X

```python
import httpx, os

def search_tweets(query: str, max_results: int = 10) -> list[dict]:
    r = httpx.get(
        "https://api.twitter.com/2/tweets/search/recent",
        headers={"Authorization": f"Bearer {os.getenv('TWITTER_BEARER_TOKEN')}"},
        params={"query": query, "max_results": max_results,
                "tweet.fields": "created_at,public_metrics"}
    )
    r.raise_for_status()
    return r.json().get("data", [])
```

## Reddit

```python
import httpx, os

def get_reddit_token() -> str:
    r = httpx.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(os.getenv("REDDIT_CLIENT_ID"), os.getenv("REDDIT_SECRET")),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": "MyBot/0.1"}
    )
    return r.json()["access_token"]

def search_reddit(subreddit: str, query: str) -> list[dict]:
    token = get_reddit_token()
    r = httpx.get(
        f"https://oauth.reddit.com/r/{subreddit}/search",
        headers={"Authorization": f"Bearer {token}", "User-Agent": "MyBot/0.1"},
        params={"q": query, "restrict_sr": True, "limit": 10}
    )
    return [{"title": p["data"]["title"], "url": p["data"]["url"]}
            for p in r.json()["data"]["children"]]
```

## Error handling

```python
try:
    result = client.get("/endpoint")
except httpx.HTTPStatusError as e:
    print(f"API error {e.response.status_code}: {e.response.text}")
except httpx.RequestError as e:
    print(f"Network error: {e}")
```

## Output convention

```python
{"platform": "upwork", "query": "python", "results": 10, "data": [...]}
```
