"""
Social Content Generator: Formats technical breakthroughs into high-signal posts.
Enforces blader/humanizer & ayghri/i-have-adhd crisp style.
"""

from typing import Dict, Any


def generate_x_thread(topic: str, hardware: str, core_insight: str, github_link: str) -> str:
    """
    Generates a structured, technical X (Twitter) thread with zero AI fluff.
    """
    return f"""🧵 1/4 Most people think autonomous drone vision requires a $500 Jetson or heavy LiDAR.
Here is how you can run real-time hardware-accelerated detection on {hardware}.

2/4 The Core Architecture:
• Compute: {hardware}
• Framework: FreeRTOS / ESP-IDF + Quantized INT8 Models
• Key Insight: {core_insight}

3/4 Why this matters for embedded engineers:
We're seeing a shift from heavy companion computers to sub-$10 microcontrollers handling both telemetry and local perception simultaneously.

4/4 Repo & blueprints:
{github_link}
If you're building in embedded robotics, star the repo and let me know what you'd build with it."""


def generate_linkedin_post(title: str, problem: str, solution: str, tech_stack: str) -> str:
    """
    Generates a clean LinkedIn engineering post.
    """
    return f"""{title}

The Problem:
{problem}

The Engineering Fix:
{solution}

Tech Stack:
{tech_stack}

Key takeaway for hardware engineers: optimize at the register and memory allocation level before throwing more compute at the problem.

#EmbeddedSystems #Robotics #Drones #TinyML #Engineering #OpenSource"""
