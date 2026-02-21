#!/usr/bin/env python3
"""
Tests for benchmark_orchestrator task and response file resolution.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from benchmark_orchestrator import BenchmarkOrchestrator


class TestBenchmarkOrchestratorResolution(unittest.TestCase):
    """Verify task/response path resolution across task layout variants."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[5]
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()

    def tearDown(self):
        os.chdir(self.original_cwd)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("benchmark_orchestrator.CodebaseManager")
    def test_loads_flat_task_and_hyphenated_response(self, mock_cm_class):
        """Flat `<task-id>.yml` + `<task-id>-responses.json` should resolve."""
        os.chdir(self.repo_root)
        mock_cm_class.return_value = Mock()

        orchestrator = BenchmarkOrchestrator(
            task_id="dark-mode-implementation",
            trials=1,
            verbose=False,
            output_dir=self.temp_dir / "out-flat",
        )

        self.assertEqual(orchestrator.task_def["id"], "dark-mode-implementation")
        self.assertIsNotNone(orchestrator.task_definition_path)
        self.assertEqual(
            orchestrator.task_definition_path.name, "dark-mode-implementation.yml"
        )
        self.assertIsNotNone(orchestrator.response_file)
        self.assertEqual(
            orchestrator.response_file.name, "dark-mode-implementation-responses.json"
        )

    @patch("benchmark_orchestrator.CodebaseManager")
    def test_loads_nested_local_task_and_responses(self, mock_cm_class):
        """Legacy local `tasks/<task-id>/task.yml` + `responses.json` should resolve."""
        task_dir = self.temp_dir / "tasks" / "custom-vibe"
        task_dir.mkdir(parents=True, exist_ok=True)

        task_def = {
            "id": "custom-vibe",
            "category": "feature-addition",
            "description": "Custom local task",
            "user_prompt": "do the thing",
        }
        task_path = task_dir / "task.yml"
        task_path.write_text(yaml.safe_dump(task_def), encoding="utf-8")

        responses_path = task_dir / "responses.json"
        responses_path.write_text(
            '{"responses": {}, "standardAutoApprove": [], "explicitDeclines": []}',
            encoding="utf-8",
        )

        os.chdir(self.temp_dir)
        mock_cm_class.return_value = Mock()

        orchestrator = BenchmarkOrchestrator(
            task_id="custom-vibe",
            trials=1,
            verbose=False,
            output_dir=self.temp_dir / "out-nested",
        )

        self.assertEqual(orchestrator.task_def["id"], "custom-vibe")
        self.assertIsNotNone(orchestrator.task_definition_path)
        self.assertEqual(
            orchestrator.task_definition_path.resolve(), task_path.resolve()
        )
        self.assertIsNotNone(orchestrator.response_file)
        self.assertEqual(orchestrator.response_file.resolve(), responses_path.resolve())

    @patch("benchmark_orchestrator.CodebaseManager")
    def test_loads_code_review_category(self, mock_cm_class):
        """`code-review` category tasks should resolve for orchestrator runs."""
        os.chdir(self.repo_root)
        mock_cm_class.return_value = Mock()

        orchestrator = BenchmarkOrchestrator(
            task_id="security-vulnerability-scan",
            trials=1,
            verbose=False,
            output_dir=self.temp_dir / "out-code-review",
        )

        self.assertEqual(orchestrator.task_def["category"], "code-review")
        self.assertIsNotNone(orchestrator.response_file)
        self.assertEqual(
            orchestrator.response_file.name,
            "security-vulnerability-scan-responses.json",
        )


if __name__ == "__main__":
    unittest.main()
