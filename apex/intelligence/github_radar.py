"""
GitHub Intelligence Radar v3:
- Authenticated (5000 req/hour via token from ~/.apex/profile.json)
- Stars filter (>10) to exclude zero-star noise
- Two separate search strategies:
    1. NEW repos (created in last 14 days) — genuine discovery
    2. ACTIVE repos (pushed in last 7 days, >50 stars) — momentum tracking
- Release monitoring for core embedded/drone stacks
- HN Algolia as Tier 3 discovery
"""

import json
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional


def _load_token() -> Optional[str]:
    """Loads GitHub token from ~/.apex/profile.json, falls back to gh CLI."""
    profile_path = Path.home() / ".apex" / "profile.json"
    if profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            token = profile.get("github_token")
            if token:
                return token
        except Exception:
            pass

    # Fallback: ask gh CLI directly
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
        token = result.stdout.strip()
        if token:
            return token
    except Exception:
        pass

    return None


def _make_headers() -> Dict[str, str]:
    token = _load_token()
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


# -------------------------------------------------------
# Two discovery modes: NEW (recently created) and ACTIVE
# -------------------------------------------------------

# Format: (search query, sort_by, description)
# Using keyword search NOT topic — topics are user-assigned and sparse on new repos
DISCOVERY_QUERIES = [
    # NEW repos — only look at what was created in the last 14 days
    ("esp32 OR esp-idf OR esp32s3", "created"),
    ("stm32 OR stm32h7 OR stm32f4", "created"),
    ("drone flight controller autonomous", "created"),
    ("px4 mavlink ardupilot", "created"),
    ("tinyml edge inference microcontroller", "created"),
    ("fpga verilog vhdl accelerator", "created"),
    ("risc-v riscv embedded", "created"),
    ("slam visual odometry lidar", "created"),
    ("ros2 gazebo robot navigation", "created"),
    ("bldc motor control simplefoc", "created"),
    ("kicad pcb schematic", "created"),
    ("lora lorawan uwb iot sensor", "created"),
]

# Key repos to monitor for new releases
MONITORED_REPOS = [
    "PX4/PX4-Autopilot",
    "ArduPilot/ardupilot",
    "ros2/ros2",
    "espressif/esp-idf",
    "espressif/arduino-esp32",
    "espressif/esp-matter",
    "SimpleFOC/Arduino-FOC",
    "betaflight/betaflight",
    "KiCad/kicad-source-mirror",
    "openpilot/openpilot",
    "qgroundcontrol/qgroundcontrol",
    "micro-ROS/micro_ros_arduino",
]


def _search_repos(
    keyword: str,
    sort: str = "created",
    min_stars: int = 5,
    days_window: int = 14,
    per_page: int = 10,
) -> List[Dict[str, Any]]:
    """
    Searches GitHub for repos matching keyword.
    sort = 'created' finds genuinely new repos.
    sort = 'updated' finds recently active repos.
    """
    cutoff = (datetime.now() - timedelta(days=days_window)).strftime("%Y-%m-%d")

    if sort == "created":
        date_filter = f"created:>{cutoff}"
    else:
        date_filter = f"pushed:>{cutoff}"

    q = f"{keyword}+{date_filter}+stars:>{min_stars}+fork:false"
    url = f"https://api.github.com/search/repositories?q={q}&sort={sort}&order=desc&per_page={per_page}"

    try:
        resp = requests.get(url, headers=_make_headers(), timeout=12)
        remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
        if resp.status_code == 403 or remaining < 5:
            print(f"[!] GitHub rate limit low ({remaining} remaining). Stopping search early.")
            return []
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception as e:
        print(f"[!] GitHub search failed: {e}")
        return []

    repos = []
    for item in data.get("items", []):
        repos.append({
            "name": item.get("full_name"),
            "description": item.get("description") or "",
            "html_url": item.get("html_url"),
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "language": item.get("language") or "Unknown",
            "updated_at": item.get("updated_at", ""),
            "created_at": item.get("created_at", ""),
            "pushed_at": item.get("pushed_at", ""),
            "topics": item.get("topics", []),
            "open_issues": item.get("open_issues_count", 0),
            "license": (item.get("license") or {}).get("spdx_id", "Unknown"),
            "is_fork": item.get("fork", False),
            "source_type": "repo",
            "source_tier": 1,
            "search_category": keyword[:40],
        })

    return repos


def fetch_new_repos(max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Discovers genuinely NEW repos (created last 14 days) across all tracked domains.
    Deduplicates by full name. Quality filter: >5 stars.
    """
    seen: Dict[str, Dict] = {}

    for keyword, sort in DISCOVERY_QUERIES:
        per_q = max(max_results // len(DISCOVERY_QUERIES), 3)
        results = _search_repos(keyword, sort=sort, min_stars=5, days_window=14, per_page=per_q)
        for r in results:
            name = r["name"]
            if name not in seen:
                seen[name] = r

    repos = list(seen.values())
    # Sort: newest first (creation date)
    repos.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return repos[:max_results]


def fetch_trending_repos(max_results: int = 15) -> List[Dict[str, Any]]:
    """
    Finds established repos with recent activity (pushed last 7 days, >50 stars).
    These are active maintained projects worth tracking.
    """
    seen: Dict[str, Dict] = {}

    # Broader combined queries for trending (less specific than discovery)
    trending_queries = [
        ("drone uav autonomous navigation", "updated"),
        ("embedded firmware microcontroller", "updated"),
        ("esp32 esp-idf iot", "updated"),
        ("tinyml edge ai inference embedded", "updated"),
        ("fpga verilog hardware accelerator", "updated"),
        ("slam robotics ros2 lidar", "updated"),
    ]

    for keyword, sort in trending_queries:
        per_q = max(max_results // len(trending_queries), 3)
        results = _search_repos(keyword, sort=sort, min_stars=50, days_window=7, per_page=per_q)
        for r in results:
            name = r["name"]
            if name not in seen:
                seen[name] = r

    repos = list(seen.values())
    repos.sort(key=lambda x: x["stars"], reverse=True)
    return repos[:max_results]


def fetch_releases(days: int = 7) -> List[Dict[str, Any]]:
    """
    Checks monitored ecosystem repos for releases in the last N days.
    """
    cutoff = datetime.now() - timedelta(days=days)
    releases = []

    for repo in MONITORED_REPOS:
        url = f"https://api.github.com/repos/{repo}/releases?per_page=5"
        try:
            resp = requests.get(url, headers=_make_headers(), timeout=10)
            if resp.status_code != 200:
                continue
            for rel in resp.json():
                published = rel.get("published_at", "")
                # Only include releases within the time window
                if published:
                    pub_dt = datetime.strptime(published[:10], "%Y-%m-%d")
                    if pub_dt < cutoff:
                        continue

                releases.append({
                    "name": f"{repo} — {rel.get('tag_name', '')}",
                    "title": rel.get("name") or rel.get("tag_name", ""),
                    "html_url": rel.get("html_url", ""),
                    "description": (rel.get("body") or "")[:600],
                    "published_at": published,
                    "prerelease": rel.get("prerelease", False),
                    "repo": repo,
                    "tag": rel.get("tag_name", ""),
                    "source_type": "release",
                    "source_tier": 1,
                    # Treat as high-interest items for known stacks
                    "stars": 9999,
                })
        except Exception:
            continue

    return releases


def fetch_hn_stories(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Hacker News Algolia — Tier 3 discovery only.
    High-engagement HN discussion threads pointing to new open-source tools.
    """
    queries = [
        "drone autonomous embedded",
        "esp32 microcontroller",
        "tinyml edge inference",
        "fpga risc-v open source",
        "ros2 robotics slam",
    ]
    stories = []
    per_q = max(max_results // len(queries), 2)

    for q in queries:
        url = f"https://hn.algolia.com/api/v1/search_by_date?query={q}&tags=story&hitsPerPage={per_q}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            for hit in resp.json().get("hits", []):
                # Skip low-engagement posts
                if (hit.get("points") or 0) < 20:
                    continue
                stories.append({
                    "title": hit.get("title", ""),
                    "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                    "description": f"HN: {hit.get('points', 0)} points, {hit.get('num_comments', 0)} comments",
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
