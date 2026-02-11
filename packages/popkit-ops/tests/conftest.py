#!/usr/bin/env python3
"""Pytest configuration for popkit-ops tests."""

import sys
from pathlib import Path

# Add shared-py to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared-py"))
