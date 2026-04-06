#!/usr/bin/env python3
"""Fetch top 10 most-commented posts from r/ZedEditor in last 10 days"""

import urllib.request
import json
import datetime

SUBREDDIT = "ZedEditor"
DAYS = 1  # yesterday's posts (last 24h)
LIMIT = 100  # fetch more to filter

def get_posts():
    url = f"https://www.reddit.com/r/{SUBREDDIT}/hot.json?limit={LIMIT}"
    headers = {"User-Agent": "Mozilla/5.0 (script:reddit-daily-digest)"}
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    
    posts = data["data"]["children"]
    return posts

def filter_recent(posts, days=10):
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    cutoff_ts = cutoff.timestamp()
    
    recent = []
    for p in posts:
        d = p["data"]
        created = d["created_utc"]
        if created >= cutoff_ts:
            num_comments = d.get("num_comments", 0)
            recent.append({
                "title": d["title"],
                "url": d["url"],
                "permalink": d["permalink"],
                "num_comments": num_comments,
                "score": d["score"],
                "created": datetime.datetime.fromtimestamp(created).strftime("%m-%d %H:%M")
            })
    return recent

def main():
    print(f"Fetching r/{SUBREDDIT} hot posts...")
    posts = get_posts()
    print(f"Got {len(posts)} posts")
    
    recent = filter_recent(posts, DAYS)
    print(f"Recent ({DAYS} days): {len(recent)} posts")
    
    # Sort by comments descending
    top10 = sorted(recent, key=lambda x: x["num_comments"], reverse=True)[:10]
    
    if not top10:
        print("No recent posts found!")
        return
    
    # Format message
    lines = [f"📮 r/{SUBREDDIT} 近10天热帖 TOP {len(top10)}\n"]
    for i, p in enumerate(top10, 1):
        comments = p["num_comments"]
        # Skip very low comment posts (often removed/nsfw)
        if comments < 2:
            continue
        title = p["title"][:60] + ("..." if len(p["title"]) > 60 else "")
        lines.append(f"{i}. {title}")
        lines.append(f"   💬 {comments} | ⬆ {p['score']} | {p['created']}")
        lines.append(f"   🔗 https://reddit.com{p['permalink']}\n")
    
    print("\n".join(lines))
    
    # Save for cron output
    with open("/tmp/reddit_digest.txt", "w") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()
