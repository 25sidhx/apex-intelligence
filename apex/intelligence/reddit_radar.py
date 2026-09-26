import feedparser
from typing import List, Dict, Any
import datetime
from bs4 import BeautifulSoup

SUBREDDITS = [
    "embedded",
    "robotics",
    "diydrones",
    "PrintedCircuitBoard",
    "RISCV"
]

def fetch_top_reddit_posts(timeframe: str = "week", max_results_per_sub: int = 5) -> List[Dict[str, Any]]:
    """
    Fetches the top posts from target subreddits using Reddit's RSS endpoint.
    Timeframe options: 'day', 'week', 'month', 'year', 'all'.
    """
    results = []
    
    for sub in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/top/.rss?t={timeframe}"
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:max_results_per_sub]:
                raw_summary = entry.get("summary", "")
                soup = BeautifulSoup(raw_summary, "html.parser")
                clean_summary = soup.get_text(separator=" ", strip=True)
                
                # Try to extract the true URL if it's a link post
                link = entry.link
                
                # Estimate upvotes based on position (RSS doesn't provide exact scores reliably)
                # But it sorts them by top, so we will assign a mock upvote count for scoring.
                
                published = entry.get("published_parsed")
                if published:
                    dt = datetime.datetime(*published[:6]).isoformat()
                else:
                    dt = datetime.datetime.now().isoformat()
                
                results.append({
                    "id": entry.link,
                    "title": f"[{sub}] {entry.title}",
                    "link": link,
                    "summary": clean_summary[:500] + ("..." if len(clean_summary) > 500 else ""),
                    "source_type": "forum",
                    "source_tier": 2,
                    "upvotes": 100, # Mock upvote value since it's from the Top feed
                    "categories": [f"r/{sub}"],
                    "created_at": dt
                })
                
        except Exception as e:
            print(f"[!] Reddit radar error for r/{sub}: {e}")
            
    return results

if __name__ == "__main__":
    posts = fetch_top_reddit_posts(timeframe="day")
    for p in posts:
        print(f"[{p['upvotes']}] {p['title']}")
