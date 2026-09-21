"""
GitHub Intelligence Radar v2: Multiple targeted queries, date filtering, release monitoring.
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


HEADERS = {"Accept": "application/vnd.github.v3+json"}

# Multiple targeted search groups instead of one broad query
SEARCH_QUERIES = [
    "topic:esp32 OR topic:esp-idf OR topic:esp32-s3",
    "topic:stm32 OR topic:stm32h7 OR topic:hal",
    "topic:drone OR topic:uav OR topic:quadcopter",
    "topic:px4 OR topic:ardupilot OR topic:betaflight",
    "topic:ros2 OR topic:ros OR topic:gazebo",
    "topic:tinyml OR topic:edge-ai OR topic:embedded-ai",
    "topic:fpga OR topic:verilog OR topic:vhdl",
    "topic:risc-v OR topic:riscv",
    "topic:simplefoc OR topic:bldc OR topic:motor-control",
    "topic:kicad OR topic:pcb-design",
    "topic:lora OR topic:lorawan",
    "topic:slam OR topic:visual-odometry",
]

# Key repos to monitor for releases
MONITORED_REPOS = [
    "PX4/PX4-Autopilot",
    "ArduPilot/ardupilot",
    "ros2/ros2",
    "espressif/esp-idf",
    "espressif/arduino-esp32",
    "SimpleFOC/Arduino-FOC",
    "betaflight/betaflight",
    "KiCad/kicad-source-mirror",
]


def _search_repos(query: str, per_page: int = 10, pushed_after: Optional[str] = None) -> List[Dict[str, Any]]:
    """Runs a single GitHub search query."""
    q = query
    if pushed_after:
        q += f" pushed:>{pushed_after}"

    url = f"https://api.github.com/search/repositories?q={q}&sort=updated&order=desc&per_page={per_page}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 403:
            # Rate limited — return empty gracefully
            return []
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []

    repos = []
    for item in data.get("items", []):
        repos.append({
            "name": item.get("full_name"),
            "description": item.get("description") or "No description.",
            "html_url": item.get("html_url"),
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "language": item.get("language") or "Unknown",
            "updated_at": item.get("updated_at"),
            "created_at": item.get("created_at"),
            "topics": item.get("topics", []),
            "open_issues": item.get("open_issues_count", 0),
            "license": (item.get("license") or {}).get("spdx_id", "Unknown"),
            "is_fork": item.get("fork", False),
            "source_type": "repo",
            "source_tier": 1,
        })

    return repos


def fetch_trending_repos(max_results: int = 15) -> List[Dict[str, Any]]:
    """
    Runs multiple targeted GitHub searches and merges results.
    Deduplicates by full repo name. Filters out forks.
    """
    # Only look at repos pushed in the last 30 days
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    per_query = max(max_results // len(SEARCH_QUERIES), 3)

    seen: Dict[str, Dict] = {}
    for query in SEARCH_QUERIES:
        results = _search_repos(query, per_page=per_query, pushed_after=cutoff)
        for r in results:
            name = r["name"]
            if name not in seen and not r["is_fork"]:
                seen[name] = r

    repos = list(seen.values())
    repos.sort(key=lambda x: x["stars"], reverse=True)
    return repos[:max_results]


def fetch_releases(max_per_repo: int = 3) -> List[Dict[str, Any]]:
    """
    Checks monitored repos for recent releases.
    """
    releases = []
    for repo in MONITORED_REPOS:
        url = f"https://api.github.com/repos/{repo}/releases?per_page={max_per_repo}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            for rel in resp.json():
                releases.append({
                    "repo": repo,
                    "tag": rel.get("tag_name", ""),
                    "name": rel.get("name", ""),
                    "published_at": rel.get("published_at", ""),
                    "html_url": rel.get("html_url", ""),
                    "body": (rel.get("body") or "")[:500],
                    "prerelease": rel.get("prerelease", False),
                    "source_type": "release",
                    "source_tier": 1,
                })
        except Exception:
            continue

    return releases


def fetch_hn_stories(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetches recent Hacker News stories matching engineering topics via Algolia API.
    Tier 3 discovery source — NOT primary evidence.
    """
    queries = ["drone autonomous", "esp32 embedded", "tinyml edge", "fpga risc-v", "ros2 robotics"]
    stories = []

    for q in queries:
        url = f"https://hn.algolia.com/api/v1/search_by_date?query={q}&tags=story&hitsPerPage={max_results // len(queries)}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            for hit in resp.json().get("hits", []):
                stories.append({
                    "title": hit.get("title", ""),
                    "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                    "points": hit.get("points", 0),
                    "num_comments": hit.get("num_comments", 0),
                    "created_at": hit.get("created_at", ""),
                    "source_type": "hn",
                    "source_tier": 3,
                })
        except Exception:
            continue

    stories.sort(key=lambda x: x.get("points", 0), reverse=True)
    return stories[:max_results]
