import feedparser
from typing import List, Dict, Any
import datetime
from bs4 import BeautifulSoup

# Hand-curated list of high-signal hardware/robotics YouTube channels
YOUTUBE_CHANNELS = {
    "Andreas Spiess": "UCu7_D0o48KbfhpEohoP7YSQ",
    "DroneBot Workshop": "UCzml9bXoEM0itbcE96CB03g",
    "GreatScott!": "UC6mIxFTvXkWQVEHPsEdflzQ",
    "Joshua Bardwell": "UCX3eCA4pYc009wG1w3qG_cA",
    "Painless360": "UCcMcucYQZ_qj_p1XmZJ8Baw",
    "James Bruton": "UCUbDcUPed50Y_7KmfCXKohA", # Heavy robotics
    "How To Mechatronics": "UCQvN4f5xJ33K3qg4IqA4tQA"
}

def fetch_youtube_videos(max_results_per_channel: int = 2) -> List[Dict[str, Any]]:
    """
    Fetches the latest videos from curated YouTube channels via RSS.
    """
    results = []
    
    for author, channel_id in YOUTUBE_CHANNELS.items():
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:max_results_per_channel]:
                raw_summary = entry.get("summary", "")
                soup = BeautifulSoup(raw_summary, "html.parser")
                clean_summary = soup.get_text(separator=" ", strip=True)
                
                published = entry.get("published_parsed")
                if published:
                    dt = datetime.datetime(*published[:6]).isoformat()
                else:
                    dt = datetime.datetime.now().isoformat()
                    
                results.append({
                    "id": entry.link,
                    "title": f"[{author}] {entry.title}",
                    "link": entry.link,
                    "summary": clean_summary[:500] + ("..." if len(clean_summary) > 500 else ""),
                    "source_type": "video",
                    "source_tier": 2, 
                    "categories": ["youtube", "video", author],
                    "created_at": dt
                })
                
        except Exception as e:
            print(f"[!] YouTube radar error for {author}: {e}")
            
    return results

if __name__ == "__main__":
    videos = fetch_youtube_videos()
    for v in videos:
        print(v['title'])
