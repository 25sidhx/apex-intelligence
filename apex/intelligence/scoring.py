"""
APEX Scoring & Personal Relevance Engine.
Calculates actionable value based on hardware constraints and technical depth.
"""

from typing import Dict, Any, Tuple

# User Constraints
HARDWARE_PROFILE = {
    "gpu": "RTX 3050",
    "boards": ["Raspberry Pi", "Arduino", "ESP32"],
    "budget": "student",
    "skills": ["embedded", "drones", "basic electronics", "intermediate video editing"]
}

def calculate_apex_score(item: Dict[str, Any]) -> float:
    """
    Calculates the APEX Score (0-10) prioritizing technical depth, open-source value, 
    and practical build value over sheer popularity.
    """
    score = 0.0
    text = (item.get("title", "") + " " + item.get("summary", "") + " " + item.get("description", "")).lower()
    
    # Base relevance to primary domains
    core_keywords = ["drone", "uav", "px4", "esp32", "stm32", "ros2", "tinyml", "slam"]
    if any(kw in text for kw in core_keywords):
        score += 3.0
        
    # Technical depth (penalize marketing fluff, reward technical specifics)
    if "tutorial" in text or "awesome-list" in text:
        score -= 1.0 # Lower value for generic collections
    if "hardware-accelerated" in text or "register" in text or "quantized" in text:
        score += 2.0
        
    # Open source / accessibility
    if "github.com" in str(item.get("url", item.get("link", ""))):
        score += 2.0
        
    # Popularity modifier (logarithmic/capped so it doesn't dominate)
    stars = item.get("stars", 0)
    if stars > 10000:
        score += 1.0
    elif stars > 500:
        score += 1.5 # Reward hidden gems gaining traction
        
    # Paper-specific scoring
    if item.get("source_type") == "paper":
        if "dataset" in text or "code available" in text or "github" in text:
            score += 2.5 # Reproducible research is king
            
    return min(max(score, 0.0), 10.0)

def evaluate_personal_relevance(item: Dict[str, Any]) -> Tuple[str, str]:
    """
    Evaluates if an item is actionable given the user's hardware (RTX 3050, Pi, etc).
    Returns (Classification, Reason)
    Classifications: IMMEDIATE, NEXT, FUTURE
    """
    text = (item.get("title", "") + " " + item.get("summary", "") + " " + item.get("description", "")).lower()
    
    # Check constraints
    if "h100" in text or "a100" in text or "64gb vram" in text:
        return "FUTURE", "Requires heavy datacenter GPU (beyond RTX 3050 4GB/8GB)."
        
    if "asics" in text or "fabrication" in text:
        return "FUTURE", "Requires silicon fabrication access."

    if any(kw in text for kw in ["esp32", "arduino", "raspberry pi", "tinyml"]):
        return "IMMEDIATE", "Hardware matches current inventory. Can build/study now."
        
    if "ros2" in text or "px4" in text:
        return "NEXT", "Requires setup (SITL/Gazebo) or minor hardware acquisition, but highly relevant."
        
    return "NEXT", "Requires further review for practical implementation."
