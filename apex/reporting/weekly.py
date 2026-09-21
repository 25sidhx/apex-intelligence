"""
APEX Weekly Intelligence Report Generator.
Strict adherence to Section 12 structural requirements.
"""

from typing import List, Dict, Any
from apex.intelligence.scoring import calculate_apex_score, evaluate_personal_relevance
from apex.memory.store import add_discovery, is_duplicate, mark_reported
import datetime

def generate_weekly_report(papers: List[Dict[str, Any]], repos: List[Dict[str, Any]]) -> str:
    """Generates the structured weekly report based on Section 12."""
    
    # In a full implementation, this would pull from the SQLite DB 
    # for all discoveries over the last 7 days.
    # For now, we process the live scan results.
    
    candidates = []
    
    for p in papers:
        p["source_type"] = "paper"
        if not is_duplicate(p["id"]): candidates.append(p)
    for r in repos:
        r["source_type"] = "repo"
        if not is_duplicate(r["html_url"]): candidates.append(r)
        
    for c in candidates:
        c["apex_score"] = calculate_apex_score(c)
        c["relevance_class"], c["relevance_reason"] = evaluate_personal_relevance(c)
        
    candidates.sort(key=lambda x: x["apex_score"], reverse=True)
    
    report = f"# APEX WEEKLY ENGINEERING INTELLIGENCE | {datetime.date.today().isoformat()}\n\n"
    
    report += "## 1. Biggest Developments\n"
    for c in candidates[:5]:
        title = c.get("title", c.get("name"))
        url = c.get("link", c.get("html_url"))
        report += f"- **{title}**: {url} (Score: {c['apex_score']:.1f})\n"
        add_discovery(c.get("id", url), c["source_type"], title, url, c["apex_score"])
        
    report += "\n## 2. New Open-Source Projects\n"
    for r in [c for c in candidates if c["source_type"] == "repo"][:5]:
        report += f"- [{r['name']}]({r['html_url']}): {r['description'][:100]}\n"
        
    report += "\n## 3. Research Papers\n"
    for p in [c for c in candidates if c["source_type"] == "paper"][:5]:
        report += f"- [{p['title']}]({p['link']}): {p['summary'][:100]}...\n"
        
    report += "\n## 4. Hardware\n"
    report += "*(Scanned from datasheets and manufacturer announcements)*\n"
    
    report += "\n## 5. Drones & Robotics\n"
    report += "*(Derived from PX4/ROS2 activity)*\n"
    
    report += "\n## 6. AI + Hardware\n"
    report += "*(Edge AI & TinyML updates)*\n"
    
    report += "\n## 7. Engineering Opportunities\n"
    report += "- Existing Technology + Unresolved Problem = Potential Project\n"
    
    report += "\n## 8. What I Should Actually Build\n"
    report += "*(Top 3 recommendations based on RTX 3050 / Pi / ESP32 inventory)*\n"
    
    report += "\n## 9. What I Should Learn\n"
    report += "*(Core concepts to bridge knowledge gaps)*\n"
    
    report += "\n## 10. Content Opportunities\n"
    report += "*(Technical carousels & social draft ideas)*\n"
    
    report += "\n## 11. Things to Ignore\n"
    report += "*(Low-signal hype filtered out by APEX)*\n"
    
    report += "\n## 12. Watchlist\n"
    report += "*(Projects to monitor for maturity)*\n"
    
    # Mark as reported
    mark_reported([c.get("id", c.get("html_url")) for c in candidates[:10]])
    
    return report
