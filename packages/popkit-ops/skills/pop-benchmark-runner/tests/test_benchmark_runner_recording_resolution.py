#!/usr/bin/env python3
"""
Tests for benchmark_runner recording collection behavior.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from benchmark_runner import BenchmarkRunner


class TestBenchmarkRunnerRecordingResolution(unittest.TestCase):
    """Verify recording collection paths for benchmark modes."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

        self.task_def = {
            "id": "test-task",
            "category": "feature-addition",
            "description": "Test task",
            "user_prompt": "Test prompt",
        }

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("benchmark_runner.CodebaseManager")
    def test_collect_recording_uses_mock_json_for_baseline_in_test_mode(
        self, mock_cm_class
    ):
        """Baseline should still find mock JSON recordings in TEST_MODE."""
        mock_cm_class.return_value = Mock()
        runner = BenchmarkRunner(
            task_def=self.task_def, trials=1, output_dir=self.temp_dir / "out"
        )

        runner.recordings_dir = self.temp_dir / "recordings"
        runner.recordings_dir.mkdir(parents=True, exist_ok=True)

        session_id = "session-123"
        recording_path = runner.recordings_dir / "mock.json"
        recording_path.write_text(
            json.dumps({"session_id": session_id, "events": [{"type": "session_end"}]}),
            encoding="utf-8",
        )

        with patch.dict("os.environ", {"TEST_MODE": "true"}):
            resolved = runner._collect_recording(
                session_id=session_id, with_popkit=False
            )

        self.assertEqual(resolved, recording_path)


if __name__ == "__main__":
    unittest.main()
