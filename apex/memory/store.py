"""
APEX Memory Engine v2: Enriched schema with entity linking, trend snapshots, and rich metadata.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent.parent / ".apex_memory.db"

_connection: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_PATH)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def init_db():
    conn = _get_conn()
    c = conn.cursor()

    # --- Main discoveries table (v2 schema) ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS discoveries (
        id TEXT PRIMARY KEY,
        source_type TEXT NOT NULL,
        source_tier INTEGER DEFAULT 1,
        title TEXT,
        url TEXT,
        author_org TEXT,
        publication_date TEXT,
        discovery_date TEXT,
        update_date TEXT,
        categories TEXT,
        technologies TEXT,
        hardware_reqs TEXT,
        software_reqs TEXT,
        license TEXT,
        maturity TEXT,
        summary TEXT,
        score_relevance REAL DEFAULT 0,
        score_novelty REAL DEFAULT 0,
        score_depth REAL DEFAULT 0,
        score_actionability REAL DEFAULT 0,
        score_source_quality REAL DEFAULT 0,
        score_hardware_compat REAL DEFAULT 0,
        score_learning REAL DEFAULT 0,
        apex_score REAL DEFAULT 0,
        score_explanation TEXT,
        action_class TEXT,
        confidence REAL DEFAULT 0,
        reported BOOLEAN DEFAULT 0,
        report_date TEXT,
        raw_data TEXT
    )
    ''')

    # --- Entity linking (paper <-> repo <-> hardware) ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS entities (
        entity_id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        canonical_name TEXT,
        created_date TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS entity_links (
        entity_id TEXT,
        discovery_id TEXT,
        relationship TEXT,
        FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
        FOREIGN KEY (discovery_id) REFERENCES discoveries(id)
    )
    ''')

    # --- Trend snapshots (track stars/forks over time) ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS trend_snapshots (
        discovery_id TEXT,
        snapshot_date TEXT,
        stars INTEGER,
        forks INTEGER,
        open_issues INTEGER,
        recent_commits INTEGER,
        FOREIGN KEY (discovery_id) REFERENCES discoveries(id)
    )
    ''')

    # --- Action queue ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS action_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discovery_id TEXT,
        action_type TEXT,
        priority TEXT,
        description TEXT,
        created_date TEXT,
        completed BOOLEAN DEFAULT 0,
        FOREIGN KEY (discovery_id) REFERENCES discoveries(id)
    )
    ''')

    conn.commit()


def _migrate_v1_to_v2():
    """Migrate old 7-column schema to new schema if needed."""
    conn = _get_conn()
    c = conn.cursor()
    # Check if new columns exist
    c.execute("PRAGMA table_info(discoveries)")
    columns = {row[1] for row in c.fetchall()}
    if "score_relevance" not in columns:
        # Old schema detected. Add new columns.
        new_cols = [
            ("source_tier", "INTEGER DEFAULT 1"),
            ("author_org", "TEXT"),
            ("publication_date", "TEXT"),
            ("update_date", "TEXT"),
            ("categories", "TEXT"),
            ("technologies", "TEXT"),
            ("hardware_reqs", "TEXT"),
            ("software_reqs", "TEXT"),
            ("license", "TEXT"),
            ("maturity", "TEXT"),
            ("summary", "TEXT"),
            ("score_relevance", "REAL DEFAULT 0"),
            ("score_novelty", "REAL DEFAULT 0"),
            ("score_depth", "REAL DEFAULT 0"),
            ("score_actionability", "REAL DEFAULT 0"),
            ("score_source_quality", "REAL DEFAULT 0"),
            ("score_hardware_compat", "REAL DEFAULT 0"),
            ("score_learning", "REAL DEFAULT 0"),
            ("score_explanation", "TEXT"),
            ("action_class", "TEXT"),
            ("confidence", "REAL DEFAULT 0"),
            ("report_date", "TEXT"),
            ("raw_data", "TEXT"),
        ]
        for col_name, col_type in new_cols:
            if col_name not in columns:
                c.execute(f"ALTER TABLE discoveries ADD COLUMN {col_name} {col_type}")
        conn.commit()


def is_duplicate(item_id: str) -> bool:
    conn = _get_conn()
    row = conn.execute("SELECT 1 FROM discoveries WHERE id = ?", (item_id,)).fetchone()
    return row is not None


def is_similar_title(title: str, threshold: float = 0.70) -> Optional[str]:
    """Check for near-duplicate titles (catches forks, mirrors, renamed repos)."""
    conn = _get_conn()
    rows = conn.execute("SELECT id, title FROM discoveries WHERE title IS NOT NULL").fetchall()
    title_lower = title.lower().strip()
    for row in rows:
        existing = (row["title"] or "").lower().strip()
        if not existing:
            continue
        # Simple token overlap ratio
        t1 = set(title_lower.split())
        t2 = set(existing.split())
        if not t1 or not t2:
            continue
        overlap = len(t1 & t2) / max(len(t1 | t2), 1)
        if overlap >= threshold:
            return row["id"]
    return None


def add_discovery(
    item_id: str,
    source_type: str,
    title: str,
    url: str,
    apex_score: float = 0.0,
    source_tier: int = 1,
    categories: Optional[List[str]] = None,
    technologies: Optional[List[str]] = None,
    summary: Optional[str] = None,
    score_breakdown: Optional[Dict[str, float]] = None,
    score_explanation: Optional[str] = None,
    action_class: Optional[str] = None,
    confidence: float = 0.5,
    author_org: Optional[str] = None,
    hardware_reqs: Optional[str] = None,
    maturity: Optional[str] = None,
    raw_data: Optional[Dict] = None,
):
    if is_duplicate(item_id):
        return

    conn = _get_conn()
    now = datetime.now().isoformat()
    sb = score_breakdown or {}

    conn.execute(
        """INSERT INTO discoveries (
            id, source_type, source_tier, title, url, author_org,
            discovery_date, categories, technologies, hardware_reqs,
            maturity, summary,
            score_relevance, score_novelty, score_depth,
            score_actionability, score_source_quality, score_hardware_compat,
            score_learning, apex_score, score_explanation,
            action_class, confidence, raw_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            item_id, source_type, source_tier, title, url, author_org,
            now,
            json.dumps(categories or []),
            json.dumps(technologies or []),
            hardware_reqs, maturity, summary,
            sb.get("relevance", 0), sb.get("novelty", 0), sb.get("depth", 0),
            sb.get("actionability", 0), sb.get("source_quality", 0),
            sb.get("hardware_compat", 0), sb.get("learning", 0),
            apex_score, score_explanation, action_class, confidence,
            json.dumps(raw_data) if raw_data else None,
        ),
    )
    conn.commit()


def add_trend_snapshot(discovery_id: str, stars: int, forks: int, open_issues: int = 0, recent_commits: int = 0):
    conn = _get_conn()
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO trend_snapshots (discovery_id, snapshot_date, stars, forks, open_issues, recent_commits) VALUES (?, ?, ?, ?, ?, ?)",
        (discovery_id, now, stars, forks, open_issues, recent_commits),
    )
    conn.commit()


def mark_reported(item_ids: List[str]):
    conn = _get_conn()
    now = datetime.now().isoformat()
    conn.executemany(
        "UPDATE discoveries SET reported = 1, report_date = ? WHERE id = ?",
        [(now, i) for i in item_ids],
    )
    conn.commit()


def get_unreported(min_score: float = 3.0, limit: int = 20) -> List[Dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM discoveries WHERE reported = 0 AND apex_score >= ? ORDER BY apex_score DESC LIMIT ?",
        (min_score, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_trend_history(discovery_id: str) -> List[Dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM trend_snapshots WHERE discovery_id = ? ORDER BY snapshot_date",
        (discovery_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def close():
    global _connection
    if _connection:
        _connection.close()
        _connection = None


# Initialize on first use
init_db()
_migrate_v1_to_v2()
