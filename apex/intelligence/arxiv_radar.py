"""
arXiv Intelligence Radar v2: Broader category coverage + targeted keyword queries.
"""

import requests
import feedparser
from typing import List, Dict, Any


HEADERS = {"User-Agent": "ApexRadar/2.0 (Embedded/Drone Intelligence Engine)"}

# Broader category set covering all user domains
CATEGORY_QUERIES = [
    "cat:cs.RO",      # Robotics
    "cat:cs.AR",      # Hardware Architecture
    "cat:eess.SP",    # Signal Processing
    "cat:eess.SY",    # Systems and Control
    "cat:cs.CV",      # Computer Vision
]

# Targeted keyword queries to catch papers the category query misses
KEYWORD_QUERIES = [
    "all:drone+AND+all:autonomous",
    "all:uav+AND+all:navigation",
    "all:tinyml+OR+all:edge+inference",
    "all:fpga+AND+all:accelerator",
    "all:slam+AND+all:visual+odometry",
    "all:swarm+AND+all:robot",
    "all:motor+control+AND+all:embedded",
    "all:lora+AND+all:iot",
]

RELEVANCE_KEYWORDS = {
    "drone", "uav", "mav", "quadrotor", "px4", "ardupilot",
    "esp32", "stm32", "rp2040", "risc-v", "fpga", "verilog", "vhdl",
    "tinyml", "edge ai", "on-device", "quantized", "microcontroller",
    "slam", "visual odometry", "gps-denied", "lidar",
    "event camera", "neuromorphic", "swarm", "ros2", "ros 2",
    "bldc", "foc", "motor control", "sensor fusion",
    "lora", "lorawan", "ble", "uwb",
    "embedded", "real-time", "rtos", "freertos",
    "computer vision", "object detection", "yolo",
    "autonomous", "navigation", "path planning",
    "pcb", "antenna", "rf", "sdr",
    "continual learning", "incremental learning",
}


def _fetch_arxiv(query: str, max_results: int) -> List[Dict[str, Any]]:
    url = f"https://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        feed = feedparser.parse(resp.text)
    except Exception:
        return []

    papers = []
    for entry in feed.entries:
        title = entry.title.replace("\n", " ").strip()
        summary = entry.summary.replace("\n", " ").strip()
        arxiv_id = entry.id.split("/abs/")[-1] if "/abs/" in entry.id else entry.id
        authors = [a.name for a in getattr(entry, "authors", [])]
        categories = [t.get("term", "") for t in getattr(entry, "tags", [])]

        combined = (title + " " + summary).lower()
        matched = [kw for kw in RELEVANCE_KEYWORDS if kw in combined]

        papers.append({
            "id": arxiv_id,
            "title": title,
            "summary": summary,
            "link": entry.link,
            "published": getattr(entry, "published", ""),
            "authors": authors[:5],
            "categories": categories,
            "matched_keywords": matched if matched else [],
            "relevance_score": len(matched),
            "source_type": "paper",
            "source_tier": 1,
        })

    return papers


def fetch_recent_papers(max_results: int = 25) -> List[Dict[str, Any]]:
    """
    Runs multiple arXiv queries (categories + targeted keywords) and merges results.
    Deduplicates by arXiv ID.
    """
    all_papers: Dict[str, Dict] = {}
    per_query = max(max_results // (len(CATEGORY_QUERIES) + len(KEYWORD_QUERIES)), 5)

    # Category-based queries
    cat_query = "+OR+".join(CATEGORY_QUERIES)
    for p in _fetch_arxiv(cat_query, per_query * len(CATEGORY_QUERIES)):
        all_papers[p["id"]] = p

    # Targeted keyword queries
    for kw_query in KEYWORD_QUERIES:
        for p in _fetch_arxiv(kw_query, per_query):
            if p["id"] not in all_papers:
                all_papers[p["id"]] = p

    papers = list(all_papers.values())
    papers.sort(key=lambda x: x["relevance_score"], reverse=True)
    return papers[:max_results]
