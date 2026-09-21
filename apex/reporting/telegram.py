"""
APEX Telegram Integration: Pushes generated reports to a Telegram chat.
"""

import requests
import json
from pathlib import Path
from typing import Optional

def get_telegram_config() -> tuple[Optional[str], Optional[str]]:
    """Retrieves the Telegram bot token and chat ID from the profile config."""
    config_path = Path.home() / ".apex" / "profile.json"
    if not config_path.exists():
        return None, None
        
    try:
        profile = json.loads(config_path.read_text(encoding="utf-8"))
        tg = profile.get("telegram", {})
        return tg.get("bot_token"), tg.get("chat_id")
    except Exception:
        return None, None

def send_telegram_message(text: str) -> bool:
    """
    Sends a Markdown-formatted message to the configured Telegram chat.
    Splits long messages if they exceed Telegram's 4096 character limit.
    """
    bot_token, chat_id = get_telegram_config()
    
    if not bot_token or not chat_id:
        print("[!] Telegram not configured. Add bot_token and chat_id to ~/.apex/profile.json")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Telegram max message length is 4096. We'll split safely if needed.
    # To keep it readable like a newsletter, we split by sections if possible.
    max_length = 4000
    parts = []
    
    while len(text) > 0:
        if len(text) <= max_length:
            parts.append(text)
            break
            
        # Try to split at a double newline
        split_idx = text.rfind("\n\n", 0, max_length)
        if split_idx == -1:
            split_idx = text.rfind("\n", 0, max_length)
            if split_idx == -1:
                split_idx = max_length
                
        parts.append(text[:split_idx])
        text = text[split_idx:].strip()

    success = True
    for part in parts:
        payload = {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code != 200:
                print(f"[!] Telegram API error: {resp.text}")
                success = False
        except Exception as e:
            print(f"[!] Failed to send Telegram message: {e}")
            success = False
            
    return success
