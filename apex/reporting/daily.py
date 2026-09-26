"""
APEX Daily Reporting Engine v2.
High-signal daily digest with engineering translation and quality gates.
"""

from typing import List, Dict, Any
from apex.intelligence.scoring import calculate_apex_score, classify_action, DEMO_SIGNALS, _count_domain_matches
from apex.memory.store import add_discovery, is_duplicate, is_similar_title, mark_reported, add_trend_snapshot
import datetime


MIN_SCORE_THRESHOLD = 18.0  # Out of 100. Aggressive enough to kill LLM slop, loose enough for real projects.


def _format_item(idx: int, item: Dict[str, Any]) -> str:
    """Formats a single discovery with engineering translation."""
    title = item.get("title", item.get("name", "Unknown"))
    url = item.get("link", item.get("html_url", ""))
    summary = item.get("summary", item.get("description", ""))[:400]
    score = item.get("apex_score", 0)
    breakdown = item.get("score_breakdown", {})
    explanation = item.get("score_explanation", "No explanation available.")
    action = item.get("action_class", "WATCH")
    source_type = item.get("source_type", "unknown").upper()
    categories = item.get("categories", [])

    out = f"## {idx}. {title}\n\n"
    out += f"**Source**: [{source_type}] {url}\n"
    if categories:
        cat_str = ", ".join(categories[:5]) if isinstance(categories, list) else str(categories)
        out += f"**Categories**: {cat_str}\n"
    out += f"**APEX Score**: {score:.0f}/100\n"
    out += f"**Action**: {action}\n\n"

    out += f"**What it is**: {summary}\n\n"

    # Engineering translation
    out += "**Why should I care?**\n"
    if breakdown.get("relevance", 0) >= 7:
        out += "Directly relevant to your primary engineering domains (embedded/drones/AI hardware).\n"
    elif breakdown.get("relevance", 0) >= 4:
        out += "Partially relevant — touches on adjacent engineering topics.\n"
    else:
        out += "Tangential relevance. Included for breadth.\n"

    out += f"\n**Can I use it?**\n"
    if action == "BUILD NOW":
        out += "YES. Compatible with your current hardware. Clone and experiment.\n"
    elif action == "BUILD WITH ADDITIONS":
        out += "PARTIAL. Needs small hardware/software additions.\n"
    elif action == "RESEARCH":
        out += "STUDY. Requires significant setup but worth understanding.\n"
    else:
        out += "WATCH. Track for maturity.\n"

    if item.get("stars"):
        out += f"\n**GitHub**: {item['stars']} stars, {item.get('forks', 0)} forks, License: {item.get('license', 'Unknown')}\n"

    out += f"\n**Score Breakdown**:\n"
    for dim, val in breakdown.items():
        out += f"  - {dim}: {val:.1f}/10\n"
    out += f"\n**Reasoning**:\n{explanation}\n\n"
    out += "---\n\n"

    return out


def generate_daily_report(papers: List[Dict[str, Any]], repos: List[Dict[str, Any]], others: List[Dict[str, Any]] = None, limit: int = 8) -> str:
    """Generates high-signal daily digest with quality gates and engineering context."""

    candidates = []
    others = others or []

    # Process papers
    for p in papers:
        p["source_type"] = p.get("source_type", "paper")
        item_id = p.get("id", p.get("link", ""))
        if is_duplicate(item_id):
            continue
        if is_similar_title(p.get("title", "")):
            continue
        candidates.append(p)

    # Process repos
    for r in repos:
        r["source_type"] = r.get("source_type", "repo")
        item_id = r.get("html_url", r.get("link", ""))
        if is_duplicate(item_id):
            continue
        if is_similar_title(r.get("name", r.get("title", ""))):
            continue
        candidates.append(r)

    # Process others (blogs, forums, videos)
    for o in others:
        item_id = o.get("id", o.get("link", ""))
        if is_duplicate(item_id):
            continue
        if is_similar_title(o.get("title", "")):
            continue
        candidates.append(o)

    # Score everything
    for c in candidates:
        text = " ".join([str(c.get("title", "")), str(c.get("summary", "")), str(c.get("description", ""))]).lower()
        apex, breakdown, explanation = calculate_apex_score(c)
        c["apex_score"] = apex
        c["score_breakdown"] = breakdown
        c["score_explanation"] = explanation
        c["action_class"] = classify_action(apex, breakdown.get("hardware_compat", 5), breakdown.get("actionability", 3), text)

    # Quality gate: filter below threshold
    candidates = [c for c in candidates if c["apex_score"] >= MIN_SCORE_THRESHOLD]

    # Sort by score
    candidates.sort(key=lambda x: x["apex_score"], reverse=True)
    top_items = candidates[:limit]

    # Format report
    today = datetime.date.today().isoformat()
    report = f"# APEX DAILY INTELLIGENCE | {today}\n\n"
    report += f"> {len(top_items)} high-signal discoveries out of {len(papers) + len(repos)} scanned. Minimum threshold: {MIN_SCORE_THRESHOLD}/100.\n\n"

    if not top_items:
        report += "*No discoveries crossed the quality threshold today. This is normal — APEX prioritizes signal over volume.*\n"
        return report

    reported_ids = []
    for idx, item in enumerate(top_items, 1):
        report += _format_item(idx, item)

        item_id = item.get("id", item.get("html_url", item.get("link", "")))
        reported_ids.append(item_id)

        # Store in memory
        add_discovery(
            item_id=item_id,
            source_type=item["source_type"],
            title=item.get("title", item.get("name", "")),
            url=item.get("link", item.get("html_url", "")),
            apex_score=item["apex_score"],
            source_tier=item.get("source_tier", 1),
            categories=item.get("categories"),
            summary=item.get("summary", item.get("description")),
            score_breakdown=item.get("score_breakdown"),
            score_explanation=item.get("score_explanation"),
            action_class=item.get("action_class"),
        )

        # Store trend snapshot for repos
        if item.get("stars"):
            add_trend_snapshot(item_id, item["stars"], item.get("forks", 0), item.get("open_issues", 0))

    mark_reported(reported_ids)

    # --- VP DEMO CORNER (scans ALL candidates, not just top N) ---
    demo_candidates = []
    for c in candidates:
        if c.get("source_type") not in ("repo", "release", "video", "blog"):
            continue
        text = " ".join([
            str(c.get("title", "")), str(c.get("name", "")),
            str(c.get("description", "")), str(c.get("summary", ""))
        ]).lower()
        demo_hits = _count_domain_matches(text, DEMO_SIGNALS)
        if demo_hits >= 2:
            c["_demo_score"] = demo_hits
            demo_candidates.append(c)

    demo_candidates.sort(key=lambda x: x.get("_demo_score", 0), reverse=True)

    if demo_candidates:
        report += "\n---\n\n## VP DEMO CORNER — Build This for Your Club\n\n"
        for d in demo_candidates[:4]:
            title = d.get("name", d.get("title", "?"))
            url = d.get("html_url", d.get("link", ""))
            stars = d.get("stars", 0)
            lang = d.get("language", "")
            desc = d.get("description", "")[:200]
            apex = d.get("apex_score", 0)
            action = d.get("action_class", "?")

            report += f"### {title}\n"
            report += f"- **Link**: {url}\n"
            if stars and stars != 9999:
                report += f"- **Stars**: {stars} | **Language**: {lang}\n"
            report += f"- **Score**: {apex:.0f}/100 | **Action**: {action}\n"
            report += f"- **What**: {desc}\n"
            report += f"- **Demo signals**: {d.get('_demo_score', 0)} matches — good for club events/shows\n\n"

    return report
