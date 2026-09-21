"""
arXiv Intelligence Radar: Queries arXiv API for recent papers in robotics, signal processing, and embedded AI.
"""

import feedparser
import requests
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any



CATEGORIES = ["cs.RO", "eess.SP", "cs.AI", "eess.SY"]
KEYWORDS = [
    "drone", "uav", "micro aerial vehicle", "gps-denied", "slam",
    "event camera", "neuromorphic", "tinyml", "microcontroller",
    "swarm", "field oriented control", "bldc", "lora", "risc-v",
    "continual learning", "on-device", "visual odometry"
]


def fetch_recent_papers(max_results: int = 25) -> List[Dict[str, Any]]:
    """
    Fetches recent papers across robotics, signal processing, and embedded AI.
    """
    query = "cat:cs.RO+OR+cat:eess.SP+OR+cat:cs.AI"
    url = f"https://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

    headers = {"User-Agent": "ApexRadar/1.0 (Embedded/Drone Intelligence Engine)"}
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        feed = feedparser.parse(resp.text)
    except Exception:
        return []

    papers = []

    for entry in feed.entries:
        title = entry.title.replace("\n", " ").strip()
        summary = entry.summary.replace("\n", " ").strip()
        link = entry.link
        published = entry.published
        authors = [a.name for a in getattr(entry, "authors", [])]

        combined_text = (title + " " + summary).lower()
        matched_keywords = [kw for kw in KEYWORDS if kw in combined_text]

        # Calculate relevance score based on keyword density
        score = min(max(len(matched_keywords) * 2 + (3 if "drone" in combined_text or "uav" in combined_text else 0), 4), 10)

        papers.append({
            "id": entry.id.split("/abs/")[-1] if "/abs/" in entry.id else entry.id,
            "title": title,
            "summary": summary,
            "link": link,
            "published": published,
            "authors": authors[:5],
            "matched_keywords": matched_keywords if matched_keywords else ["robotics/AI"],
            "relevance_score": score,
        })


    # Sort descending by relevance score
    papers.sort(key=lambda x: x["relevance_score"], reverse=True)
    return papers
