"""
APEX Multi-Factor Scoring Engine v2.
Every score has an explanation. No keyword-only scoring.
"""

import re
import json
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

# --- Hardware Profile ---
# Loaded from config, not hardcoded. Falls back to defaults.

_DEFAULT_PROFILE = {
    "gpu": "RTX 3050",
    "gpu_vram_gb": 4,
    "ram_gb": 16,
    "cpu": "unknown",
    "os": "Windows",
    "python": "3.14",
    "cuda": True,
    "boards": ["Raspberry Pi", "Arduino", "ESP32"],
    "tools": ["PlatformIO", "Arduino IDE", "KiCad"],
    "simulators": ["Gazebo"],
    "budget": "student",
    "skills": ["embedded", "drones", "electronics", "pcb", "basic-fpga", "video-editing"],
}

_profile: Optional[Dict] = None


def _load_profile() -> Dict:
    global _profile
    if _profile is not None:
        return _profile

    config_path = Path.home() / ".apex" / "profile.json"
    if config_path.exists():
        try:
            _profile = json.loads(config_path.read_text(encoding="utf-8"))
            return _profile
        except Exception:
            pass
    _profile = _DEFAULT_PROFILE.copy()
    # Auto-save default profile for user to edit
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(_profile, indent=2), encoding="utf-8")
    return _profile


# --- Domain keyword sets (more precise than flat list) ---

DOMAIN_ELECTRONICS = {
    "esp32", "stm32", "rp2040", "rp2350", "arduino", "raspberry pi", "fpga",
    "verilog", "vhdl", "systemverilog", "pcb", "kicad", "altium", "adc", "dac",
    "spi", "i2c", "uart", "gpio", "pwm", "motor control", "bldc", "foc",
    "power supply", "buck converter", "boost converter", "ldo", "battery",
    "bms", "sensor", "imu", "accelerometer", "gyroscope", "magnetometer",
    "mems", "analog", "digital", "rf", "antenna", "impedance",
}

DOMAIN_DRONE = {
    "drone", "uav", "mav", "quadrotor", "quadcopter", "multirotor", "px4",
    "ardupilot", "betaflight", "inav", "mavlink", "flight controller",
    "esc", "propeller", "thrust", "lidar", "gps-denied", "visual odometry",
    "vio", "slam", "optical flow", "barometer", "telemetry", "fpv",
    "autonomous landing", "waypoint", "geofence", "swarm",
}

DOMAIN_AI_HARDWARE = {
    "tinyml", "edge ai", "on-device", "quantized", "int8", "onnx",
    "tensorrt", "tflite", "esp-dl", "cmsis-nn", "npu", "tpu",
    "coral", "jetson", "hailo", "risc-v ai", "ai accelerator",
    "neural network", "inference", "embedded ai", "computer vision",
    "object detection", "yolo", "mobilenet", "efficientnet",
}

DOMAIN_RESEARCH = {
    "arxiv", "ieee", "acm", "conference", "journal", "preprint",
    "dataset", "benchmark", "ablation", "state-of-the-art", "sota",
    "novel", "proposed method", "baseline", "evaluation",
}

DOMAIN_OPEN_SOURCE = {
    "open source", "open-source", "mit license", "apache", "bsd",
    "gpl", "github", "gitlab", "repository", "library", "framework",
    "sdk", "api", "driver", "firmware",
}

# Things that signal LOW value
NOISE_SIGNALS = {
    "awesome list", "awesome-list", "curated list", "collection of",
    "web development", "javascript framework", "react component",
    "social media", "marketing", "seo", "cryptocurrency", "blockchain",
    "nft", "metaverse", "web3",
}

# Things that signal HYPE without substance
HYPE_SIGNALS = {
    "revolutionary", "game-changer", "disrupting", "paradigm shift",
    "unlimited potential", "next generation", "world-changing",
}

# Hardware that exceeds student capability
HEAVY_HARDWARE = {
    "h100", "a100", "v100", "dgx", "tpu v4", "tpu v5",
    "64gb vram", "128gb ram", "8x gpu", "hpc cluster",
    "fabrication", "tape-out", "asic design",
}


def _count_domain_matches(text: str, domain_set: set) -> int:
    count = 0
    for kw in domain_set:
        if kw in text:
            count += 1
    return count


def calculate_apex_score(item: Dict[str, Any]) -> Tuple[float, Dict[str, float], str]:
    """
    Returns (apex_score, score_breakdown, explanation_string).
    Score is 0-100. Each dimension is 0-10.
    """
    profile = _load_profile()
    text = " ".join([
        str(item.get("title", "")),
        str(item.get("summary", "")),
        str(item.get("description", "")),
    ]).lower()

    reasons_plus: List[str] = []
    reasons_minus: List[str] = []

    # --- 1. RELEVANCE (0-10) ---
    relevance = 0.0
    elec = _count_domain_matches(text, DOMAIN_ELECTRONICS)
    drone = _count_domain_matches(text, DOMAIN_DRONE)
    ai_hw = _count_domain_matches(text, DOMAIN_AI_HARDWARE)
    total_domain = elec + drone + ai_hw

    if total_domain >= 5:
        relevance = 9.0
        reasons_plus.append(f"Strong domain match ({total_domain} keywords across electronics/drone/AI)")
    elif total_domain >= 3:
        relevance = 7.0
        reasons_plus.append(f"Good domain match ({total_domain} keywords)")
    elif total_domain >= 1:
        relevance = 4.0
        reasons_plus.append(f"Partial domain match ({total_domain} keywords)")
    else:
        relevance = 1.0
        reasons_minus.append("No match to primary engineering domains")

    # Noise penalty
    noise = _count_domain_matches(text, NOISE_SIGNALS)
    if noise > 0:
        relevance = max(relevance - noise * 2, 0)
        reasons_minus.append(f"Contains noise signals ({noise} matches)")

    # --- 2. NOVELTY (0-10) ---
    novelty = 5.0  # Default: unknown
    if item.get("source_type") == "paper":
        novelty = 6.0
        reasons_plus.append("Research paper (likely novel)")
    stars = item.get("stars", 0)
    created = item.get("created_at", "")
    if isinstance(created, str) and "2026" in created:
        novelty += 2.0
        reasons_plus.append("Created in 2026")
    elif isinstance(created, str) and "2025" in created:
        novelty += 1.0

    # --- 3. TECHNICAL DEPTH (0-10) ---
    depth = 3.0
    depth_signals = [
        "register", "dma", "interrupt", "rtos", "freertos", "hal_",
        "peripheral", "clock tree", "pll", "adc resolution", "pwm frequency",
        "kalman filter", "ekf", "pid", "control loop", "transfer function",
        "verilog module", "testbench", "synthesis", "timing constraint",
        "quantization", "pruning", "distillation", "flops", "latency",
        "throughput", "bandwidth", "cache", "pipeline",
    ]
    depth_count = sum(1 for s in depth_signals if s in text)
    if depth_count >= 4:
        depth = 9.0
        reasons_plus.append(f"High technical depth ({depth_count} technical terms)")
    elif depth_count >= 2:
        depth = 7.0
        reasons_plus.append(f"Moderate technical depth ({depth_count} technical terms)")
    elif depth_count >= 1:
        depth = 5.0

    hype = _count_domain_matches(text, HYPE_SIGNALS)
    if hype > 0:
        depth = max(depth - hype * 2, 0)
        reasons_minus.append(f"Hype language detected ({hype} instances)")

    # --- 4. ACTIONABILITY (0-10) ---
    actionability = 3.0
    if "github.com" in str(item.get("url", item.get("link", item.get("html_url", "")))):
        actionability += 2.0
        reasons_plus.append("Has GitHub repository")
    if any(kw in text for kw in ["code available", "source code", "open source", "open-source"]):
        actionability += 2.0
        reasons_plus.append("Code appears available")
    if any(kw in text for kw in ["tutorial", "getting started", "quickstart", "example"]):
        actionability += 1.0
        reasons_plus.append("Has documentation/tutorial")
    if item.get("source_type") == "repo" and stars > 50:
        actionability += 1.0

    # --- 5. SOURCE QUALITY (0-10) ---
    source_quality = 5.0
    tier = item.get("source_tier", 1)
    if tier == 1:
        source_quality = 9.0
    elif tier == 2:
        source_quality = 7.0
    elif tier == 3:
        source_quality = 4.0
        reasons_minus.append("Tier 3 source (discovery only, not primary evidence)")

    # --- 6. HARDWARE COMPATIBILITY (0-10) ---
    hw_compat = 5.0
    owned_boards = [b.lower() for b in profile.get("boards", [])]
    for board in owned_boards:
        if board in text:
            hw_compat = 9.0
            reasons_plus.append(f"Compatible with owned hardware ({board})")
            break

    heavy = _count_domain_matches(text, HEAVY_HARDWARE)
    if heavy > 0:
        hw_compat = 1.0
        reasons_minus.append("Requires heavy hardware (datacenter GPU or fab access)")

    # --- 7. LEARNING VALUE (0-10) ---
    learning = 4.0
    if any(kw in text for kw in ["tutorial", "course", "learn", "beginner", "introduction"]):
        learning += 2.0
    if item.get("source_type") == "paper":
        learning += 1.5
    if depth >= 7:
        learning += 1.5
        reasons_plus.append("High learning value (deep technical content)")

    # --- APEX SCORE (weighted combination, 0-100) ---
    weights = {
        "relevance": 0.25,
        "novelty": 0.10,
        "depth": 0.15,
        "actionability": 0.20,
        "source_quality": 0.10,
        "hardware_compat": 0.10,
        "learning": 0.10,
    }

    breakdown = {
        "relevance": min(relevance, 10),
        "novelty": min(novelty, 10),
        "depth": min(depth, 10),
        "actionability": min(actionability, 10),
        "source_quality": min(source_quality, 10),
        "hardware_compat": min(hw_compat, 10),
        "learning": min(learning, 10),
    }

    apex = sum(breakdown[k] * weights[k] for k in weights) * 10  # Scale to 0-100

    # Hard penalty: if noise signals dominate and relevance is near zero, crush the score
    if noise >= 3 and relevance <= 2:
        apex = min(apex, 15.0)
    elif noise >= 2:
        apex *= 0.7

    # Build explanation
    explanation_parts = []
    if reasons_plus:
        explanation_parts.append("+ " + "\n+ ".join(reasons_plus))
    if reasons_minus:
        explanation_parts.append("- " + "\n- ".join(reasons_minus))
    explanation = "\n".join(explanation_parts)

    return round(apex, 1), breakdown, explanation


def classify_action(apex_score: float, hw_compat: float, actionability: float, text: str) -> str:
    """Classify into action tiers based on score dimensions."""
    heavy = _count_domain_matches(text.lower(), HEAVY_HARDWARE)
    if heavy > 0:
        return "FUTURE"
    if apex_score >= 60 and hw_compat >= 7 and actionability >= 6:
        return "BUILD NOW"
    if apex_score >= 50 and hw_compat >= 5:
        return "BUILD WITH ADDITIONS"
    if apex_score >= 40:
        return "RESEARCH"
    if apex_score >= 25:
        return "WATCH"
    return "IGNORE"
