#!/usr/bin/env python3
"""
Tests for Interactive Project Init Detection (Issue #65).

Tests monorepo detection, stack detection, quality gate detection,
premium feature detection, and question generation.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add the script to path for imports
SCRIPT_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "popkit-core"
    / "skills"
    / "pop-project-init"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

from interactive_init import (  # noqa: E402
    detect_monorepo,
    detect_onboarding,
    detect_premium_features,
    detect_quality_gates,
    detect_stack,
    generate_questions,
)

# =============================================================================
# Monorepo Detection Tests
# =============================================================================


class TestDetectMonorepo:
    """Tests for monorepo workspace detection."""

    def test_not_monorepo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = detect_monorepo(Path(tmpdir))
            assert result["is_monorepo"] is False
            assert result["workspace_type"] is None

    def test_detects_pnpm_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create pnpm-workspace.yaml
            workspace_yaml = Path(tmpdir) / "pnpm-workspace.yaml"
            workspace_yaml.write_text("packages:\n  - 'packages/*'\n")
            # Create packages dir
            (Path(tmpdir) / "packages" / "app-a").mkdir(parents=True)
            (Path(tmpdir) / "packages" / "app-b").mkdir(parents=True)

            result = detect_monorepo(Path(tmpdir))
            assert result["is_monorepo"] is True
            assert result["workspace_type"] == "pnpm"
            assert len(result["projects"]) == 2

    def test_detects_npm_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json with workspaces
            pkg = {"name": "root", "workspaces": ["packages/*"]}
            (Path(tmpdir) / "package.json").write_text(json.dumps(pkg))

            result = detect_monorepo(Path(tmpdir))
            assert result["is_monorepo"] is True
            assert result["workspace_type"] == "npm"

    def test_detects_lerna(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lerna = {"packages": ["packages/*"], "version": "independent"}
            (Path(tmpdir) / "lerna.json").write_text(json.dumps(lerna))

            result = detect_monorepo(Path(tmpdir))
            assert result["is_monorepo"] is True
            assert result["workspace_type"] == "lerna"

    def test_detects_popkit_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            workspace = {"apps": [{"name": "app1", "path": "apps/app1"}]}
            (claude_dir / "workspace.json").write_text(json.dumps(workspace))

            result = detect_monorepo(Path(tmpdir))
            assert result["is_monorepo"] is True
            assert result["workspace_type"] == "popkit"

    def test_walks_up_directory_tree(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create workspace at root
            workspace_yaml = Path(tmpdir) / "pnpm-workspace.yaml"
            workspace_yaml.write_text("packages:\n  - 'packages/*'\n")
            # Create nested project dir
            nested = Path(tmpdir) / "packages" / "my-app" / "src"
            nested.mkdir(parents=True)

            result = detect_monorepo(nested)
            assert result["is_monorepo"] is True

    def test_limits_project_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_yaml = Path(tmpdir) / "pnpm-workspace.yaml"
            workspace_yaml.write_text("packages:\n  - 'packages/*'\n")
            # Create 25 packages
            for i in range(25):
                (Path(tmpdir) / "packages" / f"pkg-{i:02d}").mkdir(parents=True)

            result = detect_monorepo(Path(tmpdir))
            assert len(result["projects"]) <= 20


# =============================================================================
# Stack Detection Tests
# =============================================================================


class TestDetectStack:
    """Tests for project stack/framework detection."""

    def test_empty_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = detect_stack(Path(tmpdir))
            assert result["detected"] is None
            assert result["confidence"] == "none"

    def test_detects_nextjs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {"dependencies": {"next": "14.0.0", "react": "18.0.0"}}
            (Path(tmpdir) / "package.json").write_text(json.dumps(pkg))

            result = detect_stack(Path(tmpdir))
            assert result["detected"] == "nextjs"
            assert result["confidence"] == "high"

    def test_detects_react_spa(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {"dependencies": {"react": "18.0.0", "react-dom": "18.0.0"}}
            (Path(tmpdir) / "package.json").write_text(json.dumps(pkg))

            result = detect_stack(Path(tmpdir))
            assert result["detected"] == "react-spa"
            assert result["confidence"] == "high"

    def test_detects_python_fastapi(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = '[project]\nname = "myapp"\n[project.dependencies]\nfastapi = ">=0.100"\n'
            (Path(tmpdir) / "pyproject.toml").write_text(content)

            result = detect_stack(Path(tmpdir))
            assert result["detected"] == "python-fastapi"
            assert result["confidence"] == "high"

    def test_detects_cloudflare_workers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "wrangler.toml").write_text('name = "my-worker"\n')

            result = detect_stack(Path(tmpdir))
            assert result["detected"] == "cloudflare-workers"
            assert result["confidence"] == "high"

    def test_detects_node_api(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {"dependencies": {"express": "4.18.0"}}
            (Path(tmpdir) / "package.json").write_text(json.dumps(pkg))

            result = detect_stack(Path(tmpdir))
            assert result["detected"] == "node-api"

    def test_suggestions_include_detected_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = {"dependencies": {"next": "14.0.0"}}
            (Path(tmpdir) / "package.json").write_text(json.dumps(pkg))

            result = detect_stack(Path(tmpdir))
            assert len(result["suggestions"]) > 0
            assert "(Detected)" in result["suggestions"][0]["label"]

    def test_suggestions_without_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = detect_stack(Path(tmpdir))
            assert len(result["suggestions"]) >= 4


# =============================================================================
# Quality Gate Detection Tests
# =============================================================================


class TestDetectQualityGates:
    """Tests for quality gate tool detection."""

    def test_empty_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = detect_quality_gates(Path(tmpdir))
            assert result["existing_tools"] == []
            assert result["recommended_level"] == "basic"

    def test_detects_eslint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".eslintrc.json").write_text("{}")

            result = detect_quality_gates(Path(tmpdir))
            assert "eslint" in result["existing_tools"]

    def test_detects_typescript(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "tsconfig.json").write_text("{}")

            result = detect_quality_gates(Path(tmpdir))
            assert "typescript" in result["existing_tools"]

    def test_detects_ruff_in_pyproject(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "[tool.ruff]\nline-length = 100\n"
            (Path(tmpdir) / "pyproject.toml").write_text(content)

            result = detect_quality_gates(Path(tmpdir))
            assert "ruff" in result["existing_tools"]

    def test_detects_ci_workflows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workflows = Path(tmpdir) / ".github" / "workflows"
            workflows.mkdir(parents=True)

            result = detect_quality_gates(Path(tmpdir))
            assert "ci-workflows" in result["existing_tools"]

    def test_recommends_standard_for_moderate_tools(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".eslintrc.json").write_text("{}")
            (Path(tmpdir) / "tsconfig.json").write_text("{}")
            (Path(tmpdir) / ".prettierrc").write_text("{}")

            result = detect_quality_gates(Path(tmpdir))
            assert result["recommended_level"] == "standard"

    def test_recommends_strict_for_many_tools(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".eslintrc.json").write_text("{}")
            (Path(tmpdir) / "tsconfig.json").write_text("{}")
            (Path(tmpdir) / ".prettierrc").write_text("{}")
            (Path(tmpdir) / "SECURITY.md").write_text("# Security")
            workflows = Path(tmpdir) / ".github" / "workflows"
            workflows.mkdir(parents=True)

            result = detect_quality_gates(Path(tmpdir))
            assert result["recommended_level"] == "strict"


# =============================================================================
# Premium Feature Detection Tests
# =============================================================================


class TestDetectPremiumFeatures:
    """Tests for premium feature detection."""

    def test_no_auth(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {}, clear=True):
                result = detect_premium_features(Path(tmpdir))
                assert result["is_authenticated"] is False
                assert result["has_voyage_key"] is False

    def test_with_popkit_api_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"POPKIT_API_KEY": "pk_test_123"}, clear=True):
                result = detect_premium_features(Path(tmpdir))
                assert result["is_authenticated"] is True

    def test_with_saved_cloud_login(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("interactive_init.has_cloud_api_key", return_value=True):
                result = detect_premium_features(Path(tmpdir))
                assert result["is_authenticated"] is True

    def test_with_voyage_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"VOYAGE_API_KEY": "va_test_123"}, clear=True):
                result = detect_premium_features(Path(tmpdir))
                assert result["has_voyage_key"] is True

    def test_reads_existing_tier(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".claude" / "popkit"
            config_dir.mkdir(parents=True)
            config = {"tier": "premium", "version": "1.0"}
            (config_dir / "config.json").write_text(json.dumps(config))

            with patch.dict(os.environ, {}, clear=True):
                result = detect_premium_features(Path(tmpdir))
                assert result["current_tier"] == "premium"


# =============================================================================
# Question Generation Tests
# =============================================================================


class TestGenerateQuestions:
    """Tests for AskUserQuestion configuration generation."""

    def _make_onboarding(self, questions=None):
        return {
            "state": {
                "schema_version": "1.0",
                "intro_seen": False,
                "telemetry_prompted": False,
                "telemetry_mode": "off",
                "completed_version": None,
            },
            "questions": questions or [],
            "question_count": len(questions or []),
        }

    def _make_monorepo(self, is_monorepo=False, workspace_type=None, projects=None):
        return {
            "is_monorepo": is_monorepo,
            "workspace_type": workspace_type,
            "workspace_root": None,
            "projects": projects or [],
        }

    def _make_stack(self, detected=None, confidence="none"):
        return {
            "detected": detected,
            "confidence": confidence,
            "indicators": {},
            "suggestions": [
                {"value": "nextjs", "label": "Next.js Application", "description": "Full-stack"},
                {"value": "python-fastapi", "label": "Python FastAPI", "description": "Async API"},
                {"value": "react-spa", "label": "React SPA", "description": "Single-page app"},
                {"value": "library", "label": "Library", "description": "Reusable package"},
            ],
        }

    def _make_quality(self, tools=None, level="basic"):
        return {"existing_tools": tools or [], "recommended_level": level}

    def _make_premium(self, authenticated=False, voyage=False):
        return {
            "is_authenticated": authenticated,
            "has_voyage_key": voyage,
            "current_tier": "free",
            "features": {},
        }

    def test_basic_questions_no_monorepo(self):
        questions = generate_questions(
            self._make_onboarding(),
            self._make_monorepo(),
            self._make_stack(),
            self._make_quality(),
            self._make_premium(),
        )
        # Should have stack + quality = 2 questions
        ids = [q["id"] for q in questions]
        assert "stack_selection" in ids
        assert "quality_gates" in ids
        assert "monorepo_config" not in ids
        assert "premium_features" not in ids

    def test_monorepo_adds_question(self):
        questions = generate_questions(
            self._make_onboarding(),
            self._make_monorepo(is_monorepo=True, workspace_type="pnpm", projects=["a", "b"]),
            self._make_stack(),
            self._make_quality(),
            self._make_premium(),
        )
        ids = [q["id"] for q in questions]
        assert "monorepo_config" in ids

    def test_premium_adds_question_when_authenticated(self):
        questions = generate_questions(
            self._make_onboarding(),
            self._make_monorepo(),
            self._make_stack(),
            self._make_quality(),
            self._make_premium(authenticated=True),
        )
        ids = [q["id"] for q in questions]
        assert "premium_features" in ids

    def test_premium_adds_question_when_voyage_key(self):
        questions = generate_questions(
            self._make_onboarding(),
            self._make_monorepo(),
            self._make_stack(),
            self._make_quality(),
            self._make_premium(voyage=True),
        )
        ids = [q["id"] for q in questions]
        assert "premium_features" in ids

    def test_stack_question_text_varies_by_confidence(self):
        # High confidence
        q_high = generate_questions(
            self._make_onboarding(),
            self._make_monorepo(),
            self._make_stack(detected="nextjs", confidence="high"),
            self._make_quality(),
            self._make_premium(),
        )
        stack_q = next(q for q in q_high if q["id"] == "stack_selection")
        assert "detected template" in stack_q["question"]

        # No detection
        q_none = generate_questions(
            self._make_onboarding(),
            self._make_monorepo(),
            self._make_stack(),
            self._make_quality(),
            self._make_premium(),
        )
        stack_q = next(q for q in q_none if q["id"] == "stack_selection")
        assert "initialize" in stack_q["question"]

    def test_quality_recommended_is_marked(self):
        questions = generate_questions(
            self._make_onboarding(),
            self._make_monorepo(),
            self._make_stack(),
            self._make_quality(level="standard"),
            self._make_premium(),
        )
        quality_q = next(q for q in questions if q["id"] == "quality_gates")
        standard_opt = next(o for o in quality_q["options"] if "Standard" in o["label"])
        assert "(Recommended)" in standard_opt["label"]

    def test_max_4_stack_options(self):
        questions = generate_questions(
            self._make_onboarding(),
            self._make_monorepo(),
            self._make_stack(),
            self._make_quality(),
            self._make_premium(),
        )
        stack_q = next(q for q in questions if q["id"] == "stack_selection")
        assert len(stack_q["options"]) <= 4

    def test_all_questions_have_required_fields(self):
        questions = generate_questions(
            self._make_onboarding(),
            self._make_monorepo(is_monorepo=True, workspace_type="pnpm", projects=["a"]),
            self._make_stack(detected="nextjs", confidence="high"),
            self._make_quality(tools=["eslint"], level="standard"),
            self._make_premium(authenticated=True),
        )
        for q in questions:
            assert "id" in q
            assert "question" in q
            assert "header" in q
            assert "options" in q
            assert len(q["options"]) >= 2

    def test_onboarding_questions_are_prepended(self):
        onboarding = self._make_onboarding(
            questions=[
                {
                    "id": "onboarding_intro",
                    "question": "Intro question",
                    "header": "PopKit intro",
                    "options": [
                        {
                            "label": "Use guided defaults (Recommended)",
                            "description": "Local first",
                        },
                        {"label": "Skip intro details", "description": "Continue"},
                    ],
                },
                {
                    "id": "telemetry_mode",
                    "question": "Telemetry question",
                    "header": "PopKit telemetry",
                    "options": [
                        {"label": "Off - local only (Recommended)", "description": "No remote"},
                        {"label": "Anonymous telemetry", "description": "Sanitized"},
                    ],
                },
            ]
        )

        questions = generate_questions(
            onboarding,
            self._make_monorepo(),
            self._make_stack(),
            self._make_quality(),
            self._make_premium(),
        )

        ids = [q["id"] for q in questions[:2]]
        assert ids == ["onboarding_intro", "telemetry_mode"]


class TestDetectOnboarding:
    """Tests for first-run onboarding detection."""

    def test_first_run_returns_intro_and_telemetry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = detect_onboarding(Path(tmpdir))

            headers = [question["header"] for question in result["questions"]]
            assert headers == ["PopKit intro", "PopKit telemetry"]
            assert result["question_count"] == 2

    def test_repeat_run_skips_onboarding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "onboarding.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "intro_seen": True,
                        "telemetry_prompted": True,
                        "telemetry_mode": "anonymous",
                        "completed_version": "1.0",
                    }
                )
            )

            result = detect_onboarding(config_dir)

            assert result["questions"] == []
            assert result["question_count"] == 0
