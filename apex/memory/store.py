"""
APEX Memory Engine: Local database to track discoveries, prevent duplicates, and manage watchlist.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_PATH = Path(".apex_memory.db")

def init_db():
    """Initializes the SQLite database schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Discoveries table (papers, repos, news)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS discoveries (
        id TEXT PRIMARY KEY,
        source_type TEXT,
        title TEXT,
        url TEXT,
        discovery_date TEXT,
        apex_score REAL,
        reported BOOLEAN DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()

def is_duplicate(item_id: str) -> bool:
    """Checks if an item has already been discovered."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM discoveries WHERE id = ?", (item_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_discovery(item_id: str, source_type: str, title: str, url: str, apex_score: float = 0.0):
    """Adds a new discovery to memory."""
    if is_duplicate(item_id):
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO discoveries (id, source_type, title, url, discovery_date, apex_score) VALUES (?, ?, ?, ?, ?, ?)",
        (item_id, source_type, title, url, now, apex_score)
    )
    conn.commit()
    conn.close()

def mark_reported(item_ids: List[str]):
    """Marks items as reported so they aren't included in future daily/weekly digests."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executemany(
        "UPDATE discoveries SET reported = 1 WHERE id = ?",
        [(i,) for i in item_ids]
    )
    conn.commit()
    conn.close()
    
# Initialize on module import
init_db()
