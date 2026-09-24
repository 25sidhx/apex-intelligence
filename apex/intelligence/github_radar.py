"""
GitHub Intelligence Radar v4:
- Domain/concept-driven queries — NOT hardware brand locked
- Discovers anything interesting across embedded, robotics, drones, AI hardware, FPGA, RF
- Two passes: NEW repos (created last 14d) + ACTIVE repos (pushed last 7d)
- Authenticated at 5000 req/hr via ~/.apex/profile.json token
- Stars quality gate: >3 for new (age matters more than stars early on), >30 for trending
- Release monitoring for core stacks
- HN Algolia Tier 3 (>20 pts only)
"""

import json
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional


# -------------------------------------------------------
# Auth
# -------------------------------------------------------

def _load_token() -> Optional[str]:
    profile_path = Path.home() / ".apex" / "profile.json"
    if profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            token = profile.get("github_token")
            if token:
                return token
        except Exception:
            pass
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
# Discovery queries — concept-driven, not brand-locked
# -------------------------------------------------------
# Format: (search query, description)
# BUDGET: 30 search requests per minute (authenticated).
# 10 NEW + 4 TRENDING + ~17 release checks = ~31. Safe margin.
# Demo queries are FIRST — they populate VP Demo Corner.

NEW_REPO_QUERIES = [
    # Demo-ready projects (VP Demo Corner) — run FIRST so rate limit doesn't kill them
    ("robot arm servo obstacle avoidance line follower",        "Demo: robot builds"),
    ("fpv drone racing swarm balancing robot",                 "Demo: drone & club"),
    ("led matrix oled display gesture control face detection",  "Demo: interactive"),
    # Core engineering domains
    ("autonomous robot slam lidar navigation control",         "Robotics & SLAM"),
    ("flight controller autopilot firmware mavlink px4",       "Drones & autopilots"),
    ("embedded firmware rtos freertos zephyr sensor",          "Embedded firmware"),
    ("motor control bldc foc inverter power electronics",      "Motor control & power"),
    ("fpga verilog vhdl risc-v accelerator open silicon",      "FPGA & open silicon"),
    ("edge inference quantization tinyml camera detection",    "Edge AI & vision"),
    ("pcb kicad schematic sdr wireless open hardware",         "Open hardware & RF"),
]

TRENDING_QUERIES = [
    ("autonomous robot embedded drone firmware",               "Autonomous & embedded"),
    ("edge ai inference fpga neural accelerator",             "Edge AI & FPGA"),
    ("servo motor arduino sensor camera raspberry",            "Maker & hardware"),
    ("slam navigation lidar swarm control",                    "Navigation & swarm"),
]

# Core ecosystem repos — watch these for releases
MONITORED_REPOS = [
    "PX4/PX4-Autopilot",
    "ArduPilot/ardupilot",
    "ros2/ros2",
    "espressif/esp-idf",
    "espressif/arduino-esp32",
    "espressif/esp-matter",
    "zephyrproject-rtos/zephyr",
    "SimpleFOC/Arduino-FOC",
    "betaflight/betaflight",
    "KiCad/kicad-source-mirror",
    "openpilot/openpilot",
    "qgroundcontrol/qgroundcontrol",
    "micro-ROS/micro_ros_arduino",
    "openocd-org/openocd",
    "gnuradio/gnuradio",
    "riscv/riscv-isa-manual",
    "tinygrad/tinygrad",
]


# -------------------------------------------------------
# Core search
# -------------------------------------------------------

def _rate_limit_ok(resp: requests.Response) -> bool:
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 100))
    if remaining < 10:
        print(f"[!] GitHub rate limit low ({remaining} remaining). Pausing queries.")
        return False
    return True


def _keywords_to_query(keyword_str: str) -> str:
    """
    Converts a space-separated keyword string into GitHub OR-syntax.
    'drone uav slam' -> 'drone+OR+uav+OR+slam'
    """
    words = [w.strip() for w in keyword_str.split() if w.strip()]
    return "+OR+".join(words)


def _search_repos(
    keyword: str,
    sort: str = "created",
    min_stars: int = 2,
    days_window: int = 14,
    per_page: int = 8,
) -> List[Dict[str, Any]]:
    cutoff = (datetime.now() - timedelta(days=days_window)).strftime("%Y-%m-%d")
    date_filter = f"created:>{cutoff}" if sort == "created" else f"pushed:>{cutoff}"

    kw_query = _keywords_to_query(keyword)
    q = f"{kw_query}+{date_filter}+stars:>{min_stars}+fork:false"
    url = f"https://api.github.com/search/repositories?q={q}&sort={sort}&order=desc&per_page={per_page}"

    try:
        resp = requests.get(url, headers=_make_headers(), timeout=12)
        if resp.status_code == 403:
            return []
        if not _rate_limit_ok(resp):
            return []
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception as e:
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
        })

    return repos


# -------------------------------------------------------
# Public API
# -------------------------------------------------------

def fetch_new_repos(max_results: int = 25) -> List[Dict[str, Any]]:
    """
    Discovers genuinely NEW repos (created last 14 days) across all engineering domains.
    Deduplicates by full name. No brand-locking — concept-driven queries only.
    """
    seen: Dict[str, Dict] = {}

    for keyword, _ in NEW_REPO_QUERIES:
        per_q = max(max_results // len(NEW_REPO_QUERIES), 3)
        results = _search_repos(keyword, sort="created", min_stars=3, days_window=14, per_page=per_q)
        for r in results:
            name = r["name"]
            if name not in seen:
                seen[name] = r

    repos = list(seen.values())
    # Sort: newest first
    repos.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return repos[:max_results]


def fetch_trending_repos(max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Finds established repos (>30 stars) with heavy recent activity (pushed last 7 days).
    Broader concepts — not limited to specific hardware.
    """
    seen: Dict[str, Dict] = {}

    for keyword, _ in TRENDING_QUERIES:
        per_q = max(max_results // len(TRENDING_QUERIES), 3)
        results = _search_repos(keyword, sort="updated", min_stars=30, days_window=7, per_page=per_q)
        for r in results:
            name = r["name"]
            if name not in seen:
                seen[name] = r

    repos = list(seen.values())
    repos.sort(key=lambda x: x["stars"], reverse=True)
    return repos[:max_results]


def fetch_releases(days: int = 7) -> List[Dict[str, Any]]:
    """
    Checks monitored ecosystem repos for releases within last N days.
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
                    "stars": 9999,
                })
        except Exception:
            continue

    return releases


def fetch_hn_stories(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    HN Algolia — Tier 3, >20 points only. Broad engineering topics.
    """
    queries = [
        "embedded systems firmware",
        "autonomous robot drone",
        "edge inference hardware",
        "fpga open source silicon",
        "motor control power electronics",
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
