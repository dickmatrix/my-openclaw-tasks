#!/usr/bin/env python3
"""Fetch top 10 most-commented posts from r/ZedEditor yesterday using Tavily search"""

import urllib.request
import json
import datetime

SUBREDDIT = "ZedEditor"
TAVILY_KEY = "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"

def search_tavily(query, max_results=10):
    url = "https://api.tavily.com/search"
    payload = {
        "query": query,
        "search_depth": "basic",
        "max_results": max_results
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TAVILY_KEY}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def get_reddit_posts():
    """Fetch hot posts from r/ZedEditor via Reddit JSON API"""
    import time
    time.sleep(2)  # avoid rate limit
    url = f"https://www.reddit.com/r/{SUBREDDIT}/hot.json?limit=50"
    headers = {"User-Agent": "Mozilla/5.0 (script:reddit-daily-digest)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return data["data"]["children"]

def filter_yesterday_posts(posts):
    """Filter posts from last 24 hours"""
    now = datetime.datetime.now(datetime.timezone.utc)
    yesterday_start = now - datetime.timedelta(days=1)
    
    recent = []
    for p in posts:
        d = p["data"]
        created = datetime.datetime.fromtimestamp(d["created_utc"], tz=datetime.timezone.utc)
        if created >= yesterday_start:
            recent.append({
                "title": d["title"],
                "url": d["url"],
                "permalink": d["permalink"],
                "num_comments": d.get("num_comments", 0),
                "score": d["score"],
                "created": created.strftime("%m-%d %H:%M")
            })
    return recent

def main():
    print(f"Fetching r/{SUBREDDIT} posts...")
    posts = get_reddit_posts()
    
    yesterday = filter_yesterday_posts(posts)
    print(f"Yesterday's posts: {len(yesterday)}")
    
    if not yesterday:
        # Fall back to last 2 days if no posts from yesterday
        print("No posts from yesterday, trying last 48h...")
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(days=2)
        yesterday = [p for p in posts if datetime.datetime.fromtimestamp(p["data"]["created_utc"], tz=datetime.timezone.utc) >= cutoff]
        print(f"Last 48h posts: {len(yesterday)}")
    
    # Sort by comments
    top10 = sorted(yesterday, key=lambda x: x["num_comments"], reverse=True)[:10]
    
    if not top10:
        print("No recent posts found!")
        with open("/tmp/reddit_digest.txt", "w") as f:
            f.write("昨天 r/ZedEditor 没有新帖子 🤔")
        return
    
    # Build response
    lines = [f"📮 r/{SUBREDDIT} 昨日热帖 TOP {len(top10)}\n"]
    for i, p in enumerate(top10, 1):
        title = p["title"][:60] + ("..." if len(p["title"]) > 60 else "")
        lines.append(f"{i}. {title}")
        lines.append(f"   💬 {p['num_comments']} | ⬆ {p['score']} | {p['created']}")
        lines.append(f"   🔗 https://reddit.com{p['permalink']}\n")
    
    output = "\n".join(lines)
    print(f"\n{output}")
    
    with open("/tmp/reddit_digest.txt", "w") as f:
        f.write(output)

if __name__ == "__main__":
    main()
