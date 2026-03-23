#!/usr/bin/env python3
"""
Bible Verse Utility for Nightly Routine

Provides encouraging Bible verses for nightly routine output.
Supports rotation modes: random, sequential, daily.

Part of PopKit Issue #71.
"""

import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class BibleVerse:
    """A Bible verse with text and reference."""

    text: str
    reference: str

    def format(self) -> str:
        """Format verse for display.

        Returns:
            Formatted string with text and reference
        """
        return f'"{self.text}"\n- {self.reference}'


# =============================================================================
# DEFAULT VERSE COLLECTION
# =============================================================================

DEFAULT_VERSES = [
    # --- Rest ---
    BibleVerse(
        text="Come to me, all you who are weary and burdened, and I will give you rest.",
        reference="Matthew 11:28",
    ),
    BibleVerse(
        text="In peace I will lie down and sleep, for you alone, Lord, make me dwell in safety.",
        reference="Psalm 4:8",
    ),
    BibleVerse(
        text="When you lie down, you will not be afraid; when you lie down, your sleep will be sweet.",
        reference="Proverbs 3:24",
    ),
    BibleVerse(
        text="In vain you rise early and stay up late, toiling for food to eat— for he grants sleep to those he loves.",
        reference="Psalm 127:2",
    ),
    BibleVerse(
        text="The Lord is my shepherd, I lack nothing. He makes me lie down in green pastures, he leads me beside quiet waters, he refreshes my soul.",
        reference="Psalm 23:1-3",
    ),
    BibleVerse(
        text="He gives strength to the weary and increases the power of the weak.",
        reference="Isaiah 40:29",
    ),
    # --- Peace ---
    BibleVerse(
        text="Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving, present your requests to God. And the peace of God, which transcends all understanding, will guard your hearts and your minds in Christ Jesus.",
        reference="Philippians 4:6-7",
    ),
    BibleVerse(
        text="I have told you these things, so that in me you may have peace. In this world you will have trouble. But take heart! I have overcome the world.",
        reference="John 16:33",
    ),
    BibleVerse(
        text="Peace I leave with you; my peace I give you. I do not give to you as the world gives. Do not let your hearts be troubled and do not be afraid.",
        reference="John 14:27",
    ),
    BibleVerse(
        text="The Lord gives strength to his people; the Lord blesses his people with peace.",
        reference="Psalm 29:11",
    ),
    BibleVerse(
        text="You will keep in perfect peace those whose minds are steadfast, because they trust in you.",
        reference="Isaiah 26:3",
    ),
    # --- Trust ---
    BibleVerse(
        text="Trust in the Lord with all your heart and lean not on your own understanding; in all your ways submit to him, and he will make your paths straight.",
        reference="Proverbs 3:5-6",
    ),
    BibleVerse(
        text="Cast all your anxiety on him because he cares for you.",
        reference="1 Peter 5:7",
    ),
    BibleVerse(
        text="For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.",
        reference="Jeremiah 29:11",
    ),
    BibleVerse(
        text="The Lord himself goes before you and will be with you; he will never leave you nor forsake you. Do not be afraid; do not be discouraged.",
        reference="Deuteronomy 31:8",
    ),
    BibleVerse(
        text="And we know that in all things God works for the good of those who love him, who have been called according to his purpose.",
        reference="Romans 8:28",
    ),
    # --- Strength & Renewal ---
    BibleVerse(
        text="But those who hope in the Lord will renew their strength. They will soar on wings like eagles; they will run and not grow weary, they will walk and not be faint.",
        reference="Isaiah 40:31",
    ),
    BibleVerse(
        text="Be still, and know that I am God.",
        reference="Psalm 46:10",
    ),
    BibleVerse(
        text="I can do all this through him who gives me strength.",
        reference="Philippians 4:13",
    ),
    BibleVerse(
        text="The Lord is my light and my salvation— whom shall I fear? The Lord is the stronghold of my life— of whom shall I be afraid?",
        reference="Psalm 27:1",
    ),
    # --- Gratitude & Completion ---
    BibleVerse(
        text="This is the day that the Lord has made; let us rejoice and be glad in it.",
        reference="Psalm 118:24",
    ),
    BibleVerse(
        text="Give thanks to the Lord, for he is good; his love endures forever.",
        reference="Psalm 107:1",
    ),
    BibleVerse(
        text="Being confident of this, that he who began a good work in you will carry it on to completion until the day of Christ Jesus.",
        reference="Philippians 1:6",
    ),
    BibleVerse(
        text="Whatever you do, work at it with all your heart, as working for the Lord, not for human masters.",
        reference="Colossians 3:23",
    ),
    BibleVerse(
        text="Let us not become weary in doing good, for at the proper time we will reap a harvest if we do not give up.",
        reference="Galatians 6:9",
    ),
]


# =============================================================================
# VERSE SELECTOR
# =============================================================================


class VerseSelector:
    """Selects verses according to rotation mode."""

    def __init__(
        self,
        verses: list[BibleVerse] | None = None,
        rotation: str = "random",
        state_file: Path | None = None,
    ):
        """Initialize verse selector.

        Args:
            verses: List of verses (uses DEFAULT_VERSES if None)
            rotation: Rotation mode ('random', 'sequential', 'daily')
            state_file: Path to state file for sequential/daily tracking
        """
        self.verses = verses or DEFAULT_VERSES
        self.rotation = rotation
        if state_file is None:
            from .plugin_data import get_plugin_data_dir

            state_file = get_plugin_data_dir() / "verse-state.json"
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load state from file.

        Returns:
            State dict with 'index' and 'date'
        """
        if not self.state_file.exists():
            return {"index": 0, "date": None}

        try:
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {"index": 0, "date": None}

    def _save_state(self) -> None:
        """Save state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def select(self) -> BibleVerse:
        """Select a verse according to rotation mode.

        Returns:
            Selected BibleVerse
        """
        if self.rotation == "random":
            return random.choice(self.verses)

        elif self.rotation == "sequential":
            index = self.state.get("index", 0) % len(self.verses)
            verse = self.verses[index]

            # Update state for next time
            self.state["index"] = (index + 1) % len(self.verses)
            self._save_state()

            return verse

        elif self.rotation == "daily":
            today = datetime.now().date().isoformat()
            last_date = self.state.get("date")

            # If it's a new day, move to next verse
            if last_date != today:
                index = self.state.get("index", 0)
                self.state["index"] = (index + 1) % len(self.verses)
                self.state["date"] = today
                self._save_state()

            index = self.state.get("index", 0) % len(self.verses)
            return self.verses[index]

        else:
            # Fallback to random
            return random.choice(self.verses)


# =============================================================================
# CONFIGURATION
# =============================================================================


def load_verse_config() -> dict:
    """Load verse configuration from popkit config.

    Returns:
        Config dict with 'enabled', 'rotation', and 'custom_verses'
    """
    from .plugin_data import get_plugin_data_dir

    config_file = get_plugin_data_dir() / "config.json"
    if not config_file.exists():
        return {
            "enabled": True,
            "rotation": "random",
            "custom_verses": [],
        }

    try:
        with open(config_file, encoding="utf-8") as f:
            config = json.load(f)
            verse_config = config.get("nightly_routine", {}).get("bible_verse", {})
            return {
                "enabled": verse_config.get("enabled", True),
                "rotation": verse_config.get("rotation", "random"),
                "custom_verses": verse_config.get("custom_verses", []),
            }
    except (OSError, json.JSONDecodeError):
        return {
            "enabled": True,
            "rotation": "random",
            "custom_verses": [],
        }


def get_nightly_verse() -> str | None:
    """Get formatted verse for nightly routine.

    Returns:
        Formatted verse string, or None if disabled
    """
    config = load_verse_config()

    if not config["enabled"]:
        return None

    # Use custom verses if provided
    verses = DEFAULT_VERSES
    if config["custom_verses"]:
        verses = [
            BibleVerse(text=v["text"], reference=v["reference"]) for v in config["custom_verses"]
        ]

    selector = VerseSelector(verses=verses, rotation=config["rotation"])
    verse = selector.select()
    return verse.format()


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    # Test the verse selector
    print("=== Bible Verse Selector Test ===\n")

    print("Random selection:")
    for i in range(3):
        verse = get_nightly_verse()
        print(f"\n{i + 1}. {verse}")

    print("\n\n=== Configuration Options ===")
    print(
        """
Add to .claude/popkit/config.json:

{
  "nightly_routine": {
    "bible_verse": {
      "enabled": true,
      "rotation": "random",  // or "sequential", "daily"
      "custom_verses": []
    }
  }
}

Custom verse format:
{
  "custom_verses": [
    {
      "text": "Your verse text here",
      "reference": "Book Chapter:Verse"
    }
  ]
}
"""
    )
