"""
APEX Daily Reporting Engine.
Generates strict 5-10 item high-signal daily digests.
"""

from typing import List, Dict, Any
from apex.intelligence.scoring import calculate_apex_score, evaluate_personal_relevance
from apex.memory.store import add_discovery, is_duplicate, mark_reported
import datetime

def generate_daily_report(papers: List[Dict[str, Any]], repos: List[Dict[str, Any]], limit: int = 10) -> str:
    """Filters, scores, and formats the top daily discoveries."""
    
    candidates = []
    
    # Process papers
    for p in papers:
        p["source_type"] = "paper"
        if not is_duplicate(p["id"]):
            candidates.append(p)
            
    # Process repos
    for r in repos:
        r["source_type"] = "repo"
        r_id = r["html_url"]
        if not is_duplicate(r_id):
            candidates.append(r)
            
    # Score and filter
    for c in candidates:
        c["apex_score"] = calculate_apex_score(c)
        c["relevance_class"], c["relevance_reason"] = evaluate_personal_relevance(c)
        
    # Sort by APEX score
    candidates.sort(key=lambda x: x["apex_score"], reverse=True)
    top_items = candidates[:limit]
    
    # Format Report
    report = f"# APEX DAILY INTELLIGENCE | {datetime.date.today().isoformat()}\n\n"
    report += "> High-signal embedded, drone, and research discoveries.\n\n"
    
    if not top_items:
        report += "*No new high-signal discoveries crossed the threshold today.*\n"
        return report
        
    reported_ids = []
    
    for idx, item in enumerate(top_items, 1):
        if item["source_type"] == "paper":
            title = item["title"]
            url = item["link"]
            what_happened = item["summary"][:300] + "..."
            item_id = item["id"]
        else:
            title = item["name"]
            url = item["html_url"]
            what_happened = item["description"]
            item_id = item["html_url"]
            
        reported_ids.append(item_id)
        add_discovery(item_id, item["source_type"], title, url, item["apex_score"])
        
        report += f"## {idx}. {title}\n"
        report += f"- **Category**: [{item['source_type'].upper()}]\n"
        report += f"- **Source**: {url}\n"
        report += f"- **What Happened**: {what_happened}\n"
        report += f"- **APEX Score**: {item['apex_score']:.1f}/10.0\n"
        report += f"- **Action**: {item['relevance_class']} - {item['relevance_reason']}\n\n"
        
    # Mark as reported so they don't show up again
    mark_reported(reported_ids)
    
    return report
