"""
APEX Weekly Intelligence Report Generator v2.
All sections populated from scored data. No placeholders. No AI slop.
"""

from typing import List, Dict, Any
from apex.intelligence.scoring import calculate_apex_score, classify_action, DEMO_SIGNALS, _count_domain_matches
from apex.memory.store import add_discovery, is_duplicate, is_similar_title, mark_reported, add_trend_snapshot
import datetime


MIN_SCORE = 12.0  # Lower threshold — scorer handles the noise, not the gate


def _categorize(items: List[Dict]) -> Dict[str, List[Dict]]:
    """Splits items into domain buckets based on matched keywords and text content."""
    buckets: Dict[str, List[Dict]] = {
        "electronics": [],
        "drones": [],
        "ai_hardware": [],
        "research": [],
        "open_source": [],
        "hardware_news": [],
    }
    elec_kws = {"esp32", "stm32", "rp2040", "fpga", "verilog", "pcb", "kicad", "sensor", "adc", "spi", "i2c", "motor", "bldc", "lora", "rf", "antenna", "battery", "bms"}
    drone_kws = {"drone", "uav", "px4", "ardupilot", "betaflight", "flight controller", "mavlink", "slam", "gps-denied", "visual odometry", "swarm", "fpv", "autonomous"}
    ai_kws = {"tinyml", "edge ai", "quantized", "onnx", "tensorrt", "npu", "tpu", "jetson", "hailo", "inference", "yolo", "object detection", "computer vision"}

    for item in items:
        text = " ".join([str(item.get("title", "")), str(item.get("summary", "")), str(item.get("description", ""))]).lower()
        placed = False
        if any(kw in text for kw in drone_kws):
            buckets["drones"].append(item)
            placed = True
        if any(kw in text for kw in elec_kws):
            buckets["electronics"].append(item)
            placed = True
        if any(kw in text for kw in ai_kws):
            buckets["ai_hardware"].append(item)
            placed = True
        if item.get("source_type") == "paper":
            buckets["research"].append(item)
            placed = True
        if item.get("source_type") == "repo":
            buckets["open_source"].append(item)
            placed = True
        if item.get("source_type") in ("blog", "forum", "video"):
            buckets["hardware_news"].append(item)
            placed = True

    return buckets


def generate_weekly_report(papers: List[Dict[str, Any]], repos: List[Dict[str, Any]], others: List[Dict[str, Any]] = None) -> str:
    """Generates 12-section weekly report with real data in every section."""

    candidates = []
    others = others or []

    for p in papers:
        p["source_type"] = p.get("source_type", "paper")
        if not is_duplicate(p.get("id", "")) and not is_similar_title(p.get("title", "")):
            candidates.append(p)
    for r in repos:
        r["source_type"] = r.get("source_type", "repo")
        if not is_duplicate(r.get("html_url", "")) and not is_similar_title(r.get("name", "")):
            candidates.append(r)
    for o in others:
        if not is_duplicate(o.get("id", o.get("link", ""))) and not is_similar_title(o.get("title", "")):
            candidates.append(o)

    # Score
    for c in candidates:
        text = " ".join([str(c.get("title", "")), str(c.get("summary", "")), str(c.get("description", ""))]).lower()
        apex, breakdown, explanation = calculate_apex_score(c)
        c["apex_score"] = apex
        c["score_breakdown"] = breakdown
        c["score_explanation"] = explanation
        c["action_class"] = classify_action(apex, breakdown.get("hardware_compat", 5), breakdown.get("actionability", 3), text)

    # Filter
    candidates = [c for c in candidates if c["apex_score"] >= MIN_SCORE]
    candidates.sort(key=lambda x: x["apex_score"], reverse=True)
    buckets = _categorize(candidates)

    today = datetime.date.today().isoformat()
    report = f"# APEX WEEKLY ENGINEERING INTELLIGENCE | {today}\n\n"

    # --- Section 1: Top Discoveries ---
    report += "## 1. Top Discoveries\n\n"
    for c in candidates[:5]:
        title = c.get("title", c.get("name"))
        url = c.get("link", c.get("html_url"))
        report += f"- **{title}** | Score: {c['apex_score']:.0f}/100 | Action: {c['action_class']}\n"
        report += f"  {url}\n"
        report += f"  {c.get('score_explanation', '').split(chr(10))[0]}\n\n"

    # --- Section 2: Open-Source Projects ---
    report += "## 2. New Open-Source Projects\n\n"
    for r in buckets["open_source"][:5]:
        report += f"- [{r.get('name', '?')}]({r.get('html_url', '')}) | {r.get('stars', 0)} stars | {r.get('language', '?')} | License: {r.get('license', '?')}\n"
        report += f"  {r.get('description', '')[:120]}\n\n"
    if not buckets["open_source"]:
        report += "*No new high-signal repos this week.*\n\n"

    # --- Section 3: Research Papers ---
    report += "## 3. Research Papers\n\n"
    for p in buckets["research"][:5]:
        report += f"- **{p.get('title', '?')}**\n"
        report += f"  {p.get('link', '')} | Keywords: {', '.join(p.get('matched_keywords', [])[:5])}\n"
        report += f"  {p.get('summary', '')[:200]}...\n\n"
    if not buckets["research"]:
        report += "*No papers matched the relevance threshold this week.*\n\n"

    # --- Section 4: Hardware / Electronics ---
    report += "## 4. Electronics & Hardware\n\n"
    for e in buckets["electronics"][:5]:
        title = e.get("title", e.get("name"))
        report += f"- **{title}** | Score: {e['apex_score']:.0f}/100\n"
    if not buckets["electronics"]:
        report += "*No high-signal electronics discoveries this week.*\n\n"

    # --- Section 5: Drones & Robotics ---
    report += "\n## 5. Drones & Robotics\n\n"
    for d in buckets["drones"][:5]:
        title = d.get("title", d.get("name"))
        report += f"- **{title}** | Score: {d['apex_score']:.0f}/100 | Action: {d['action_class']}\n"
    if not buckets["drones"]:
        report += "*No drone/robotics discoveries crossed the threshold.*\n\n"

    # --- Section 6: AI + Hardware ---
    report += "\n## 6. AI + Hardware\n\n"
    for a in buckets["ai_hardware"][:5]:
        title = a.get("title", a.get("name"))
        report += f"- **{title}** | Score: {a['apex_score']:.0f}/100\n"
    if not buckets["ai_hardware"]:
        report += "*No edge AI / TinyML discoveries this week.*\n\n"

    # --- Section 7: Hardware News, Blogs & Demos ---
    report += "\n## 7. Hardware News, Blogs & Demos\n\n"
    for hn in buckets["hardware_news"][:8]:
        title = hn.get("title", "?")
        report += f"- **{title}** | {hn.get('source_type').upper()}\n"
        report += f"  {hn.get('link', '')}\n"
    if not buckets["hardware_news"]:
        report += "*No hardware blogs, Reddit discussions, or videos this week.*\n\n"

    # --- Section 8: Engineering Opportunities ---
    report += "\n## 8. Engineering Opportunities\n\n"
    build_now = [c for c in candidates if c["action_class"] == "BUILD NOW"]
    build_add = [c for c in candidates if c["action_class"] == "BUILD WITH ADDITIONS"]
    if build_now or build_add:
        for b in (build_now + build_add)[:3]:
            title = b.get("title", b.get("name"))
            report += f"- **{title}**: {b.get('action_class')} — {b.get('score_explanation', '').split(chr(10))[0]}\n"
    else:
        report += "*No BUILD NOW opportunities this week. Check RESEARCH items for deeper dives.*\n"

    # --- Section 8: What I Should Build ---
    report += "\n## 8. What I Should Actually Build\n\n"
    if build_now:
        for b in build_now[:3]:
            title = b.get("title", b.get("name"))
            url = b.get("link", b.get("html_url"))
            report += f"### {title}\n"
            report += f"- **URL**: {url}\n"
            report += f"- **Why**: {b.get('score_explanation', '').split(chr(10))[0]}\n"
            report += f"- **Score**: {b['apex_score']:.0f}/100\n\n"
    else:
        report += "*No items scored high enough across actionability + hardware compatibility for immediate builds. Check Section 7 for near-ready items.*\n"

    # --- Section 9: What I Should Learn ---
    report += "\n## 9. What I Should Learn\n\n"
    high_learning = sorted(candidates, key=lambda x: x.get("score_breakdown", {}).get("learning", 0), reverse=True)[:3]
    for h in high_learning:
        title = h.get("title", h.get("name"))
        learn_score = h.get("score_breakdown", {}).get("learning", 0)
        report += f"- **{title}** (Learning value: {learn_score:.1f}/10)\n"
    if not high_learning:
        report += "*No high-learning-value items this week.*\n"

    # --- Section 10: Content Opportunities ---
    report += "\n## 10. Content Opportunities\n\n"
    for c in candidates[:3]:
        title = c.get("title", c.get("name"))
        report += f"- **{title}** — Could become a carousel/thread explaining the core technical idea.\n"

    # --- Section 11: Things to Ignore ---
    report += "\n## 11. Things to Ignore\n\n"
    ignored = [c for c in candidates if c["action_class"] == "IGNORE"]
    if ignored:
        for i in ignored[:3]:
            report += f"- {i.get('title', i.get('name'))}: Low signal. {i.get('score_explanation', '').split(chr(10))[0]}\n"
    else:
        report += "*Nothing was flagged as pure noise this week.*\n"

    # --- Section 12: Watchlist ---
    report += "\n## 12. Watchlist\n\n"
    watched = [c for c in candidates if c["action_class"] == "WATCH"]
    for w in watched[:5]:
        title = w.get("title", w.get("name"))
        report += f"- **{title}** | Score: {w['apex_score']:.0f}/100 — Promising but needs maturity.\n"
    if not watched:
        report += "*No items in watch status.*\n"

    # --- VP DEMO CORNER ---
    report += "\n---\n\n## VP DEMO CORNER — Build This for Your Club\n"
    report += "> Open-source projects you can replicate, demo at events, or use as a foundation for club showcases.\n\n"

    # Find demo-ready candidates: open source repos + action BUILD NOW or BUILD WITH ADDITIONS
    # + has demo signals (visually impressive, physical, interactive)
    demo_candidates = []
    for c in candidates:
        if c.get("source_type") not in ("repo", "release"):
            continue
        if c.get("action_class") not in ("BUILD NOW", "BUILD WITH ADDITIONS"):
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
        for demo in demo_candidates[:5]:
            title = demo.get("name", demo.get("title", "?"))
            url = demo.get("html_url", demo.get("link", ""))
            stars = demo.get("stars", 0)
            lang = demo.get("language", "")
            desc = demo.get("description", "")[:180]
            apex = demo.get("apex_score", 0)

            report += f"### {title}\n"
            report += f"- **Repo**: {url}\n"
            if stars:
                report += f"- **Stars**: {stars} | **Language**: {lang}\n"
            report += f"- **APEX Score**: {apex:.0f}/100\n"
            report += f"- **What it is**: {desc}\n"
            report += f"- **Why demo it**: Matches {demo.get('_demo_score', 0)} demo/event signals. "
            report += "Physically demonstrable, open hardware, or interactive — good for club event or show.\n"
            if demo.get("action_class") == "BUILD NOW":
                report += "- **Effort**: Should work on your current hardware with minimal additions.\n"
            else:
                report += "- **Effort**: May need small hardware additions — check the repo README.\n"
            report += "\n"
    else:
        # Fallback: show any BUILD NOW/WITH ADDITIONS repos even without explicit demo signals
        fallback = [c for c in candidates
                    if c.get("source_type") in ("repo", "release")
                    and c.get("action_class") in ("BUILD NOW", "BUILD WITH ADDITIONS")][:3]
        if fallback:
            for f in fallback:
                title = f.get("name", f.get("title", "?"))
                url = f.get("html_url", f.get("link", ""))
                desc = f.get("description", "")[:150]
                report += f"- **{title}**: {url}\n  {desc}\n\n"
        else:
            report += "*No demo-ready open-source projects found this week. All hardware repos needed too many additions.*\n"

    # --- BONUS: IF I ONLY HAVE 5 HOURS ---
    report += "\n---\n\n## IF I ONLY HAVE 5 HOURS THIS WEEK\n\n"
    top3 = candidates[:3]
    for idx, t in enumerate(top3, 1):
        title = t.get("title", t.get("name"))
        url = t.get("link", t.get("html_url"))
        report += f"{idx}. **{title}** — {t['action_class']}\n   {url}\n\n"
    if not top3:
        report += "*No actionable items this week.*\n"

    # Persist
    reported_ids = []
    for c in candidates[:20]:
        item_id = c.get("id", c.get("html_url", c.get("link", "")))
        reported_ids.append(item_id)
        add_discovery(
            item_id=item_id,
            source_type=c["source_type"],
            title=c.get("title", c.get("name", "")),
            url=c.get("link", c.get("html_url", "")),
            apex_score=c["apex_score"],
            source_tier=c.get("source_tier", 1),
            categories=c.get("categories"),
            summary=c.get("summary", c.get("description")),
            score_breakdown=c.get("score_breakdown"),
            score_explanation=c.get("score_explanation"),
            action_class=c.get("action_class"),
        )
        if c.get("stars"):
            add_trend_snapshot(item_id, c["stars"], c.get("forks", 0), c.get("open_issues", 0))

    mark_reported(reported_ids)
    return report
