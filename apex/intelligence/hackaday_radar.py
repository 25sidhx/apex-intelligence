import feedparser
from typing import List, Dict, Any
import datetime
from bs4 import BeautifulSoup

HACKADAY_RSS_URL = "https://hackaday.com/blog/feed/"

def fetch_hackaday_posts(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetches the latest hardware projects and blogs from Hackaday via RSS.
    """
    results = []
    
    try:
        feed = feedparser.parse(HACKADAY_RSS_URL)
        
        for entry in feed.entries[:max_results]:
            # Clean HTML from description
            raw_summary = entry.get("summary", entry.get("description", ""))
            soup = BeautifulSoup(raw_summary, "html.parser")
            clean_summary = soup.get_text(separator=" ", strip=True)
            
            # Publish date handling
            published = entry.get("published_parsed")
            if published:
                dt = datetime.datetime(*published[:6]).isoformat()
            else:
                dt = datetime.datetime.now().isoformat()
                
            results.append({
                "id": entry.link,
                "title": entry.title,
                "link": entry.link,
                "summary": clean_summary[:500] + ("..." if len(clean_summary) > 500 else ""),
                "source_type": "blog",
                "source_tier": 2, # Respectable editorial source
                "categories": ["hackaday", "open hardware"],
                "created_at": dt
            })
            
    except Exception as e:
        print(f"[!] Hackaday radar error: {e}")
        
    return results

if __name__ == "__main__":
    posts = fetch_hackaday_posts()
    for p in posts:
        print(p['title'])
