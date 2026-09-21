"""
GitHub Intelligence Radar: Queries GitHub API for active repositories in embedded systems, drones, and edge AI.
"""

import requests
from typing import List, Dict, Any


SEARCH_TOPICS = [
    "esp32-p4",
    "px4-autopilot",
    "ardupilot",
    "ros2-drone",
    "tinyml-microcontroller",
    "simplefoc",
    "lorawan-embedded",
    "neuromorphic-vision",
]


def fetch_trending_repos(max_results: int = 15) -> List[Dict[str, Any]]:
    """
    Scouts active GitHub repositories based on robotics and embedded topics.
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    repos = []

    # Search for repos with embedded and drone keywords created or pushed recently
    query = "topic:esp32 OR topic:drone OR topic:px4 OR topic:tinyml OR topic:ros2"
    url = f"https://api.github.com/search/repositories?q={query}&sort=updated&order=desc&per_page={max_results}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                repos.append({
                    "name": item.get("full_name"),
                    "description": item.get("description") or "No description provided.",
                    "html_url": item.get("html_url"),
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "language": item.get("language") or "C/C++",
                    "updated_at": item.get("updated_at"),
                    "topics": item.get("topics", []),
                })
    except Exception as e:
        # Graceful fallback in case of network/rate-limit constraints
        pass

    return repos
