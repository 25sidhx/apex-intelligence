"""
Humanizer Engine: Eliminates robotic AI cliches and enforces crisp engineering voice.
Inspired by blader/humanizer.
"""

import re
from typing import Dict, List, Tuple


AI_CLICHES = [
    r"\bdelve\b",
    r"\bdelving\b",
    r"\btestament to\b",
    r"\bit's important to remember\b",
    r"\bfurthermore\b",
    r"\bmoreover\b",
    r"\btapestry\b",
    r"\bbeacon\b",
    r"\bunleash\b",
    r"\bharnessing the power\b",
    r"\bin today's fast-paced world\b",
    r"\bgame-changer\b",
    r"\bin conclusion\b",
    r"\bpivotal role\b",
]


def audit_text(text: str) -> Dict[str, Any]:
    """
    Scans input text for generic AI cliches and outputs severity + line locations.
    """
    matches: List[Tuple[str, int]] = []
    lines = text.splitlines()

    for idx, line in enumerate(lines, 1):
        for pattern in AI_CLICHES:
            found = re.findall(pattern, line, re.IGNORECASE)
            for f in found:
                matches.append((f, idx))

    return {
        "cliche_count": len(matches),
        "flagged_instances": matches,
        "is_clean": len(matches) == 0,
        "score": max(10 - len(matches) * 2, 0),
    }


def clean_text(text: str) -> str:
    """
    Substitutes common cliches with direct, professional engineering phrasing.
    """
    replacements = {
        r"\bdelve into\b": "examine",
        r"\bdelves into\b": "examines",
        r"\bfurthermore,\b": "Additionally,",
        r"\bmoreover,\b": "Also,",
        r"\bharnessing the power of\b": "using",
        r"\ba testament to\b": "evidence of",
        r"\bpivotal role\b": "key role",
        r"\bgame-changer\b": "significant improvement",
    }

    cleaned = text
    for pat, rep in replacements.items():
        cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)

    return cleaned
