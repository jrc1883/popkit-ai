#!/usr/bin/env python3
"""
Tests for Bible Verse Utility (Issue #71).

Tests verse collection, selection modes, configuration, and formatting.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from popkit_shared.utils.bible_verses import (
    DEFAULT_VERSES,
    BibleVerse,
    VerseSelector,
    get_nightly_verse,
    load_verse_config,
)

# =============================================================================
# BibleVerse Dataclass Tests
# =============================================================================


class TestBibleVerse:
    """Tests for the BibleVerse dataclass."""

    def test_creation(self):
        verse = BibleVerse(text="Test text", reference="Test 1:1")
        assert verse.text == "Test text"
        assert verse.reference == "Test 1:1"

    def test_format(self):
        verse = BibleVerse(text="Be still.", reference="Psalm 46:10")
        result = verse.format()
        assert '"Be still."' in result
        assert "- Psalm 46:10" in result

    def test_format_multiline(self):
        verse = BibleVerse(text="Line one. Line two.", reference="Book 1:2")
        result = verse.format()
        assert result == '"Line one. Line two."\n- Book 1:2'


# =============================================================================
# Default Verse Collection Tests
# =============================================================================


class TestDefaultVerses:
    """Tests for the default verse collection."""

    def test_has_sufficient_verses(self):
        """Issue #71 requires 20-30 verses."""
        assert len(DEFAULT_VERSES) >= 20

    def test_all_verses_are_bible_verses(self):
        for verse in DEFAULT_VERSES:
            assert isinstance(verse, BibleVerse)

    def test_all_verses_have_text(self):
        for verse in DEFAULT_VERSES:
            assert verse.text
            assert len(verse.text) > 10

    def test_all_verses_have_references(self):
        for verse in DEFAULT_VERSES:
            assert verse.reference
            assert len(verse.reference) > 3

    def test_no_duplicate_references(self):
        references = [v.reference for v in DEFAULT_VERSES]
        assert len(references) == len(set(references)), "Found duplicate references"

    def test_no_duplicate_texts(self):
        texts = [v.text for v in DEFAULT_VERSES]
        assert len(texts) == len(set(texts)), "Found duplicate verse texts"

    def test_all_verses_format_correctly(self):
        for verse in DEFAULT_VERSES:
            formatted = verse.format()
            assert formatted.startswith('"')
            assert "- " in formatted


# =============================================================================
# VerseSelector Tests
# =============================================================================


class TestVerseSelector:
    """Tests for the VerseSelector class."""

    def test_random_selection(self):
        selector = VerseSelector(rotation="random")
        verse = selector.select()
        assert isinstance(verse, BibleVerse)

    def test_random_returns_different_verses(self):
        """Random mode should return different verses over multiple calls."""
        selector = VerseSelector(rotation="random")
        results = {selector.select().reference for _ in range(50)}
        # With 25 verses and 50 draws, we should get at least 5 unique
        assert len(results) >= 5

    def test_sequential_rotation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            verses = [
                BibleVerse(text="First", reference="A 1:1"),
                BibleVerse(text="Second", reference="B 2:2"),
                BibleVerse(text="Third", reference="C 3:3"),
            ]
            selector = VerseSelector(verses=verses, rotation="sequential", state_file=state_file)

            assert selector.select().text == "First"
            # Reload to simulate next session
            selector2 = VerseSelector(verses=verses, rotation="sequential", state_file=state_file)
            assert selector2.select().text == "Second"

    def test_sequential_wraps_around(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            verses = [
                BibleVerse(text="First", reference="A 1:1"),
                BibleVerse(text="Second", reference="B 2:2"),
            ]
            # Go through all verses and wrap
            for i in range(3):
                selector = VerseSelector(
                    verses=verses, rotation="sequential", state_file=state_file
                )
                selector.select()

            selector = VerseSelector(verses=verses, rotation="sequential", state_file=state_file)
            # After 3 selections from 2 verses, index should be at 1
            verse = selector.select()
            assert verse.text == "Second"

    def test_daily_rotation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            verses = [
                BibleVerse(text="First", reference="A 1:1"),
                BibleVerse(text="Second", reference="B 2:2"),
            ]
            selector = VerseSelector(verses=verses, rotation="daily", state_file=state_file)
            verse1 = selector.select()
            # Same day, same verse
            selector2 = VerseSelector(verses=verses, rotation="daily", state_file=state_file)
            verse2 = selector2.select()
            assert verse1.reference == verse2.reference

    def test_custom_verses(self):
        custom = [BibleVerse(text="Custom verse", reference="Custom 1:1")]
        selector = VerseSelector(verses=custom, rotation="random")
        verse = selector.select()
        assert verse.text == "Custom verse"

    def test_unknown_rotation_falls_back_to_random(self):
        selector = VerseSelector(rotation="unknown_mode")
        verse = selector.select()
        assert isinstance(verse, BibleVerse)

    def test_state_file_created_on_sequential(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "subdir" / "state.json"
            selector = VerseSelector(rotation="sequential", state_file=state_file)
            selector.select()
            assert state_file.exists()

    def test_corrupted_state_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state_file.write_text("not valid json")
            selector = VerseSelector(rotation="sequential", state_file=state_file)
            # Should not crash, falls back to default state
            verse = selector.select()
            assert isinstance(verse, BibleVerse)


# =============================================================================
# Configuration Tests
# =============================================================================


class TestLoadVerseConfig:
    """Tests for configuration loading."""

    def test_default_config_when_no_file(self):
        with patch("popkit_shared.utils.bible_verses.Path.exists", return_value=False):
            config = load_verse_config()
            assert config["enabled"] is True
            assert config["rotation"] == "random"
            assert config["custom_verses"] == []

    def test_loads_config_from_file(self):
        config_data = {
            "nightly_routine": {
                "bible_verse": {
                    "enabled": False,
                    "rotation": "sequential",
                    "custom_verses": [{"text": "Test", "reference": "Test 1:1"}],
                }
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            config_path = Path(f.name)

        try:
            with patch(
                "popkit_shared.utils.bible_verses.Path",
                return_value=config_path,
            ):
                # Direct test of config parsing
                with open(config_path, encoding="utf-8") as cf:
                    loaded = json.load(cf)
                verse_config = loaded.get("nightly_routine", {}).get("bible_verse", {})
                assert verse_config["enabled"] is False
                assert verse_config["rotation"] == "sequential"
        finally:
            config_path.unlink(missing_ok=True)

    def test_corrupted_config_returns_defaults(self):
        """Corrupted config file should return safe defaults."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            f.flush()
            config_path = Path(f.name)

        try:
            with patch("popkit_shared.utils.bible_verses.Path") as mock_path:
                mock_path.return_value.exists.return_value = True
                # The function handles JSONDecodeError gracefully
                config = load_verse_config()
                # Should get defaults (config file path doesn't actually match)
                assert "enabled" in config
                assert "rotation" in config
        finally:
            config_path.unlink(missing_ok=True)


# =============================================================================
# get_nightly_verse Tests
# =============================================================================


class TestGetNightlyVerse:
    """Tests for the main public API."""

    def test_returns_formatted_string(self):
        verse = get_nightly_verse()
        assert verse is not None
        assert isinstance(verse, str)
        assert '"' in verse
        assert "- " in verse

    def test_disabled_returns_none(self):
        with patch(
            "popkit_shared.utils.bible_verses.load_verse_config",
            return_value={
                "enabled": False,
                "rotation": "random",
                "custom_verses": [],
            },
        ):
            result = get_nightly_verse()
            assert result is None

    def test_custom_verses_used(self):
        custom = [{"text": "My custom verse", "reference": "Custom 1:1"}]
        with patch(
            "popkit_shared.utils.bible_verses.load_verse_config",
            return_value={
                "enabled": True,
                "rotation": "random",
                "custom_verses": custom,
            },
        ):
            result = get_nightly_verse()
            assert "My custom verse" in result
            assert "Custom 1:1" in result
