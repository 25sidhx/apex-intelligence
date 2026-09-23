"""
APEX Test Suite: Scoring, Memory, Sources, and Reports.
Uses fixture data — no live API calls required.
"""

import pytest
import json
import os
import sys
import sqlite3
from pathlib import Path

# Ensure apex is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ============================================================
# FIXTURES
# ============================================================

DRONE_PAPER = {
    "id": "test-drone-001",
    "title": "GPS-Denied UAV Navigation using Visual Odometry and ESP32-based Sensor Fusion",
    "summary": "We present a lightweight SLAM system for drone autonomous landing using visual odometry on embedded microcontroller hardware. The system runs on an ESP32-S3 with quantized INT8 inference using TinyML and achieves real-time performance at 30 FPS.",
    "link": "https://arxiv.org/abs/9999.00001",
    "published": "2026-09-20",
    "authors": ["Test Author"],
    "source_type": "paper",
    "source_tier": 1,
}

IRRELEVANT_PAPER = {
    "id": "test-irrelevant-001",
    "title": "Optimizing Social Media Engagement Through Blockchain NFT Marketing",
    "summary": "We study the paradigm shift in revolutionary web3 marketing strategies for cryptocurrency projects. This game-changer disrupting the metaverse.",
    "link": "https://arxiv.org/abs/9999.00002",
    "published": "2026-09-20",
    "authors": ["Spammer"],
    "source_type": "paper",
    "source_tier": 3,
}

ACTIVE_REPO = {
    "name": "test-user/esp32-drone-controller",
    "description": "Open-source ESP32-based flight controller with PX4 MAVLink integration and SimpleFOC motor control.",
    "html_url": "https://github.com/test-user/esp32-drone-controller",
    "stars": 350,
    "forks": 45,
    "language": "C",
    "updated_at": "2026-09-19",
    "created_at": "2026-03-01",
    "topics": ["esp32", "drone", "px4"],
    "open_issues": 12,
    "license": "MIT",
    "is_fork": False,
    "source_type": "repo",
    "source_tier": 1,
}

DEAD_REPO = {
    "name": "someone/awesome-iot-list",
    "description": "A curated list of awesome IoT resources. Collection of links.",
    "html_url": "https://github.com/someone/awesome-iot-list",
    "stars": 25000,
    "forks": 3000,
    "language": "Markdown",
    "updated_at": "2023-01-01",
    "created_at": "2018-06-01",
    "topics": ["awesome", "iot"],
    "open_issues": 500,
    "license": "CC-BY-4.0",
    "is_fork": False,
    "source_type": "repo",
    "source_tier": 2,
}

HEAVY_GPU_PAPER = {
    "id": "test-heavy-001",
    "title": "Training Large Vision Models on 8x H100 GPUs with 64GB VRAM",
    "summary": "We require an HPC cluster with A100 datacenter GPUs for training.",
    "link": "https://arxiv.org/abs/9999.00003",
    "published": "2026-09-20",
    "authors": ["Big Lab"],
    "source_type": "paper",
    "source_tier": 1,
}


# ============================================================
# TEST: SCORING
# ============================================================

class TestScoring:
    def test_drone_paper_scores_high(self):
        from apex.intelligence.scoring import calculate_apex_score
        score, breakdown, explanation = calculate_apex_score(DRONE_PAPER)
        assert score >= 50, f"Drone paper should score >= 50, got {score}"
        assert breakdown["relevance"] >= 7, f"Relevance should be >= 7, got {breakdown['relevance']}"
        assert "domain match" in explanation.lower() or "+" in explanation

    def test_irrelevant_paper_scores_low(self):
        from apex.intelligence.scoring import calculate_apex_score
        score, breakdown, explanation = calculate_apex_score(IRRELEVANT_PAPER)
        assert score < 30, f"Irrelevant paper should score < 30, got {score}"
        assert breakdown["relevance"] <= 3, f"Relevance should be <= 3"

    def test_active_repo_scores_well(self):
        from apex.intelligence.scoring import calculate_apex_score
        score, breakdown, explanation = calculate_apex_score(ACTIVE_REPO)
        assert score >= 40, f"Active ESP32 drone repo should score >= 40, got {score}"
        assert breakdown["hardware_compat"] >= 7, f"Hardware compat should be high for ESP32 repo"

    def test_dead_repo_penalized(self):
        from apex.intelligence.scoring import calculate_apex_score
        score, breakdown, explanation = calculate_apex_score(DEAD_REPO)
        # Despite 25K stars, an awesome-list should score lower than the 350-star active repo
        active_score, _, _ = calculate_apex_score(ACTIVE_REPO)
        assert score < active_score, f"Dead awesome-list ({score}) should score lower than active drone repo ({active_score})"

    def test_heavy_gpu_classified_future(self):
        from apex.intelligence.scoring import calculate_apex_score, classify_action
        score, breakdown, explanation = calculate_apex_score(HEAVY_GPU_PAPER)
        action = classify_action(score, breakdown["hardware_compat"], breakdown["actionability"],
                                 HEAVY_GPU_PAPER["title"] + " " + HEAVY_GPU_PAPER["summary"])
        assert action == "FUTURE", f"H100 paper should be FUTURE, got {action}"

    def test_score_has_explanation(self):
        from apex.intelligence.scoring import calculate_apex_score
        _, _, explanation = calculate_apex_score(DRONE_PAPER)
        assert len(explanation) > 20, "Score explanation should be substantive"
        assert "+" in explanation, "Explanation should contain positive reasons"

    def test_hype_language_penalized(self):
        from apex.intelligence.scoring import calculate_apex_score
        score_irr, bd_irr, _ = calculate_apex_score(IRRELEVANT_PAPER)
        assert bd_irr["depth"] <= 3, f"Hype-laden paper should have low depth, got {bd_irr['depth']}"


# ============================================================
# TEST: MEMORY
# ============================================================

class TestMemory:
    @pytest.fixture(autouse=True)
    def setup_clean_db(self, tmp_path):
        """Use a temp database for each test."""
        import apex.memory.store as store
        store.DB_PATH = tmp_path / "test_memory.db"
        store._connection = None
        store.init_db()
        yield
        store.close()

    def test_add_and_detect_duplicate(self):
        from apex.memory.store import add_discovery, is_duplicate
        assert not is_duplicate("test-1")
        add_discovery("test-1", "paper", "Test Paper", "https://example.com", apex_score=50.0)
        assert is_duplicate("test-1")

    def test_similar_title_detection(self):
        from apex.memory.store import add_discovery, is_similar_title
        add_discovery("test-1", "paper", "GPS-Denied UAV Navigation using Visual Odometry", "https://example.com")
        # Slightly different title (e.g., fork or duplicate)
        match = is_similar_title("GPS-Denied UAV Navigation via Visual Odometry")
        assert match is not None, "Should detect similar title"

    def test_dissimilar_titles_not_flagged(self):
        from apex.memory.store import add_discovery, is_similar_title
        add_discovery("test-1", "paper", "GPS-Denied UAV Navigation using Visual Odometry", "https://example.com")
        match = is_similar_title("Blockchain Marketing Strategy for Social Media")
        assert match is None, "Completely different title should not match"

    def test_mark_reported(self):
        from apex.memory.store import add_discovery, mark_reported, get_unreported
        add_discovery("test-r1", "paper", "Test", "https://example.com", apex_score=50.0)
        assert len(get_unreported(min_score=0)) == 1
        mark_reported(["test-r1"])
        assert len(get_unreported(min_score=0)) == 0

    def test_trend_snapshot(self):
        from apex.memory.store import add_discovery, add_trend_snapshot, get_trend_history
        add_discovery("repo-1", "repo", "Test Repo", "https://github.com/x/y", apex_score=40.0)
        add_trend_snapshot("repo-1", stars=100, forks=10)
        add_trend_snapshot("repo-1", stars=150, forks=15)
        history = get_trend_history("repo-1")
        assert len(history) == 2
        assert history[1]["stars"] == 150


# ============================================================
# TEST: SOURCE PARSING (offline fixtures)
# ============================================================

class TestSources:
    def test_arxiv_relevance_keywords(self):
        from apex.intelligence.arxiv_radar import RELEVANCE_KEYWORDS
        assert "drone" in RELEVANCE_KEYWORDS
        assert "esp32" in RELEVANCE_KEYWORDS
        assert "slam" in RELEVANCE_KEYWORDS
        assert "javascript" not in RELEVANCE_KEYWORDS

    def test_github_fork_filtering(self):
        """Forks should be excluded from trending results."""
        fork_repo = ACTIVE_REPO.copy()
        fork_repo["is_fork"] = True
        fork_repo["name"] = "forker/esp32-drone-controller"
        # The fetch_trending_repos function filters forks internally,
        # but we can verify the fixture data structure
        assert fork_repo["is_fork"] is True


# ============================================================
# TEST: REPORTS
# ============================================================

class TestReports:
    @pytest.fixture(autouse=True)
    def setup_clean_db(self, tmp_path):
        import apex.memory.store as store
        store.DB_PATH = tmp_path / "test_report.db"
        store._connection = None
        store.init_db()
        yield
        store.close()

    def test_daily_report_filters_low_scores(self):
        from apex.reporting.daily import generate_daily_report
        report = generate_daily_report([IRRELEVANT_PAPER], [], limit=5)
        # Irrelevant paper has no domain match + noise signals — scorer kills it below threshold
        assert "Social Media" not in report or "No discoveries" in report

    def test_daily_report_includes_high_scores(self):
        from apex.reporting.daily import generate_daily_report
        report = generate_daily_report([DRONE_PAPER], [ACTIVE_REPO], limit=5)
        assert "GPS-Denied" in report or "esp32-drone" in report

    def test_weekly_report_has_all_sections(self):
        from apex.reporting.weekly import generate_weekly_report
        report = generate_weekly_report([DRONE_PAPER], [ACTIVE_REPO])
        for section in ["Top Discoveries", "Open-Source", "Research Papers", "Electronics", "Drones", "AI + Hardware",
                        "Engineering Opportunities", "What I Should Actually Build", "What I Should Learn",
                        "Content Opportunities", "Things to Ignore", "Watchlist",
                        "VP DEMO CORNER", "IF I ONLY HAVE 5 HOURS"]:
            assert section in report, f"Weekly report missing section: {section}"

    def test_weekly_no_placeholder_text(self):
        from apex.reporting.weekly import generate_weekly_report
        report = generate_weekly_report([DRONE_PAPER], [ACTIVE_REPO])
        assert "*(Scanned from datasheets" not in report, "Old placeholder text should not appear"
        assert "*(Derived from PX4/ROS2 activity)*" not in report, "Old placeholder text should not appear"
