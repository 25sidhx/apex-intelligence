"""
Context Mode Filter: Compresses raw compiler/log output to prevent LLM context bloating.
Inspired by mksglu/context-mode.
"""

import re
from typing import List, Dict, Any


def filter_compiler_output(raw_output: str, max_lines: int = 40) -> Dict[str, Any]:
    """
    Parses compiler logs (GCC, Clang, PlatformIO, colcon) and extracts
    errors, fatal errors, and critical warnings.
    """
    lines = raw_output.splitlines()
    total_lines = len(lines)

    error_patterns = [
        re.compile(r"error:", re.IGNORECASE),
        re.compile(r"fatal error:", re.IGNORECASE),
        re.compile(r"undefined reference to", re.IGNORECASE),
        re.compile(r"ninja: build stopped:", re.IGNORECASE),
        re.compile(r"\[build\] failed", re.IGNORECASE),
        re.compile(r"SyntaxError:", re.IGNORECASE),
    ]
    warning_patterns = [
        re.compile(r"warning:", re.IGNORECASE),
    ]

    extracted_errors: List[str] = []
    extracted_warnings: List[str] = []

    for line in lines:
        if any(p.search(line) for p in error_patterns):
            extracted_errors.append(line.strip())
        elif any(p.search(line) for p in warning_patterns):
            if len(extracted_warnings) < 15:
                extracted_warnings.append(line.strip())

    compressed_summary = {
        "total_lines": total_lines,
        "error_count": len(extracted_errors),
        "warning_count": len(extracted_warnings),
        "critical_errors": extracted_errors[:max_lines],
        "sample_warnings": extracted_warnings[:10],
        "compression_ratio": f"{(1.0 - (len(extracted_errors) + len(extracted_warnings)) / max(total_lines, 1)) * 100:.1f}%",
    }
    return compressed_summary
