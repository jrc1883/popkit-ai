#!/usr/bin/env python3
"""
Integration tests for PopKit stateless hook patterns.

Tests the PreToolUse and PostToolUse hook logic with real context objects,
verifying end-to-end behavior through the JSON protocol.

Note: The hook files in popkit-core/hooks/ use bare imports that are designed
for standalone subprocess execution. For pytest, we test the same logic using
the proper package imports from popkit_shared.utils.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.context_carrier import HookContext, create_context, update_context
from popkit_shared.utils.stateless_hook import StatelessHook, run_hook

# =============================================================================
# Hook Implementations (mirroring popkit-core/hooks/ for testing)
# These are direct copies of the hook logic, using correct package imports.
# =============================================================================


class PreToolUseStateless(StatelessHook):
    """Pre-tool-use hook: safety checks and recommendations.

    Mirrors popkit-core/hooks/pre_tool_use_stateless.py
    """

    BLOCKED_COMMANDS = [
        r"rm\s+-rf\s+/",
        r"sudo\s+rm\s+-rf",
        r"DROP\s+DATABASE",
        r"TRUNCATE\s+TABLE",
        r">\s*/dev/sd[a-z]",
        r"mkfs\.",
        r":(){:|:&};:",
    ]

    SENSITIVE_PATHS = [
        r"\.env",
        r"\.ssh/",
        r"\.aws/credentials",
        r"\.gnupg/",
        r"id_rsa",
        r"\.npmrc",
        r"\.pypirc",
    ]

    CODE_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java"]

    def process(self, ctx: HookContext) -> HookContext:
        tool_name = ctx.tool_name
        tool_input = ctx.tool_input

        violations = self._check_safety_violations(tool_name, tool_input)
        safety_check = {"passed": len(violations) == 0, "violations": violations}
        recommendations = self._get_recommendations(tool_name, tool_input)
        action = "block" if violations else "continue"

        return self.update_context(
            ctx,
            hook_output=(
                "pre_tool_use",
                {
                    "action": action,
                    "safety_check": safety_check,
                    "recommendations": recommendations,
                },
            ),
        )

    def _check_safety_violations(self, tool_name: str, tool_input: Dict[str, Any]) -> List[str]:
        violations = []
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            for pattern in self.BLOCKED_COMMANDS:
                if re.search(pattern, command, re.IGNORECASE):
                    violations.append(f"Blocked command pattern: {pattern}")
        if tool_name in ("Write", "Edit", "Read"):
            file_path = tool_input.get("file_path", "")
            for pattern in self.SENSITIVE_PATHS:
                if re.search(pattern, file_path):
                    violations.append(f"Sensitive path access: {pattern}")
        return violations

    def _get_recommendations(self, tool_name: str, tool_input: Dict[str, Any]) -> List[str]:
        recommendations = []
        if tool_name in ("Write", "Edit"):
            file_path = tool_input.get("file_path", "")
            for ext in self.CODE_EXTENSIONS:
                if file_path.endswith(ext):
                    recommendations.append(
                        "Consider running code-reviewer after file modifications"
                    )
                    break
            if "test" in file_path.lower() or "spec" in file_path.lower():
                recommendations.append("Consider running test-writer-fixer for test modifications")
            if file_path.endswith((".json", ".yaml", ".yml", ".toml")):
                recommendations.append("Config file modified - verify no secrets exposed")
        return recommendations


class PostToolUseStateless(StatelessHook):
    """Post-tool-use hook: followups and truncation detection.

    Mirrors popkit-core/hooks/post_tool_use_stateless.py
    """

    FOLLOWUP_RULES = {
        "Write": ["suggest_code_review", "check_for_tests"],
        "Edit": ["suggest_code_review", "run_linter"],
        "Bash": ["validate_output", "check_side_effects"],
        "Read": [],
        "Glob": [],
        "Grep": [],
    }

    TRUNCATION_THRESHOLD = 50000

    def process(self, ctx: HookContext) -> HookContext:
        tool_name = ctx.tool_name
        tool_result = ctx.tool_result

        followups = self._get_followups(tool_name, tool_result)
        truncation_warning = self._check_truncation(tool_result)

        if tool_result:
            message = self.build_tool_result(
                tool_use_id=f"toolu_{ctx.session_id}", content=tool_result
            )
            ctx = self.update_context(ctx, message=message)

        return self.update_context(
            ctx,
            hook_output=(
                "post_tool_use",
                {
                    "action": "continue",
                    "followups": followups,
                    "truncation_warning": truncation_warning,
                },
            ),
        )

    def _get_followups(self, tool_name: str, tool_result) -> List[str]:
        return self.FOLLOWUP_RULES.get(tool_name, [])

    def _check_truncation(self, result) -> str:
        if result and len(result) > self.TRUNCATION_THRESHOLD:
            return "Result may be truncated. Consider streaming or pagination."
        return ""


# =============================================================================
# PreToolUseStateless Integration Tests
# =============================================================================


class TestPreToolUseSafetyChecks:
    """Test PreToolUseStateless safety violation detection with real contexts."""

    def test_allows_safe_bash_command(self):
        """Safe bash commands should pass with no violations."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "ls -la"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "continue"
        assert safety["safety_check"]["passed"] is True
        assert len(safety["safety_check"]["violations"]) == 0

    def test_blocks_rm_rf_root(self):
        """rm -rf / should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "rm -rf /"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"
        assert safety["safety_check"]["passed"] is False
        assert len(safety["safety_check"]["violations"]) > 0

    def test_blocks_sudo_rm_rf(self):
        """sudo rm -rf should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "sudo rm -rf /home"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"
        assert safety["safety_check"]["passed"] is False

    def test_blocks_drop_database(self):
        """DROP DATABASE should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "psql -c 'DROP DATABASE production'"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"
        assert safety["safety_check"]["passed"] is False

    def test_blocks_truncate_table(self):
        """TRUNCATE TABLE should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "mysql -e 'TRUNCATE TABLE users'"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"

    def test_blocks_fork_bomb(self):
        """Fork bomb pattern should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": ":(){:|:&};:"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"

    def test_blocks_mkfs(self):
        """mkfs commands should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "mkfs.ext4 /dev/sda1"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"

    def test_blocks_device_write(self):
        """Writing to disk devices should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "cat data > /dev/sda"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"

    def test_allows_normal_git_commands(self):
        """Normal git commands should be allowed."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "git status"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "continue"
        assert safety["safety_check"]["passed"] is True

    def test_allows_npm_commands(self):
        """Normal npm commands should be allowed."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "npm test"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "continue"

    def test_allows_python_commands(self):
        """Python commands should be allowed."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "python -m pytest tests/ -v"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "continue"


class TestPreToolUseSensitivePaths:
    """Test PreToolUseStateless sensitive path detection."""

    def test_blocks_env_file_write(self):
        """Writing to .env files should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Write",
            tool_input={"file_path": "/project/.env"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"
        assert safety["safety_check"]["passed"] is False

    def test_blocks_ssh_key_read(self):
        """Reading SSH keys should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "/home/user/.ssh/id_rsa"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"

    def test_blocks_aws_credentials(self):
        """Reading AWS credentials should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "/home/user/.aws/credentials"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"

    def test_blocks_gnupg_directory(self):
        """Reading .gnupg files should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "/home/user/.gnupg/private-keys-v1.d/key"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"

    def test_blocks_npmrc_edit(self):
        """Editing .npmrc should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Edit",
            tool_input={"file_path": "/home/user/.npmrc"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"

    def test_blocks_pypirc_write(self):
        """Writing .pypirc should be blocked."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Write",
            tool_input={"file_path": "/home/user/.pypirc"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "block"

    def test_allows_normal_file_read(self):
        """Normal file reads should be allowed."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "/project/src/index.ts"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "continue"
        assert safety["safety_check"]["passed"] is True

    def test_allows_normal_file_write(self):
        """Normal file writes should be allowed."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Write",
            tool_input={"file_path": "/project/src/utils.ts"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "continue"

    def test_bash_not_checked_for_sensitive_paths(self):
        """Bash tool should not trigger sensitive path checks."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "cat .env"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        safety = result.hook_outputs["pre_tool_use"]
        assert safety["action"] == "continue"


class TestPreToolUseRecommendations:
    """Test PreToolUseStateless recommendation generation."""

    def test_recommends_code_review_for_ts_files(self):
        """Should recommend code review for TypeScript file modifications."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Write",
            tool_input={"file_path": "/project/src/auth.ts"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        recommendations = result.hook_outputs["pre_tool_use"]["recommendations"]
        assert any("code-reviewer" in r for r in recommendations)

    def test_recommends_code_review_for_python_files(self):
        """Should recommend code review for Python file modifications."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Edit",
            tool_input={"file_path": "/project/src/main.py"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        recommendations = result.hook_outputs["pre_tool_use"]["recommendations"]
        assert any("code-reviewer" in r for r in recommendations)

    def test_recommends_code_review_for_jsx_files(self):
        """Should recommend code review for JSX file modifications."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Write",
            tool_input={"file_path": "/project/src/App.jsx"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        recommendations = result.hook_outputs["pre_tool_use"]["recommendations"]
        assert any("code-reviewer" in r for r in recommendations)

    def test_recommends_test_runner_for_test_files(self):
        """Should recommend test runner for test file modifications."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Write",
            tool_input={"file_path": "/project/tests/test_auth.py"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        recommendations = result.hook_outputs["pre_tool_use"]["recommendations"]
        assert any("test-writer-fixer" in r for r in recommendations)

    def test_recommends_test_runner_for_spec_files(self):
        """Should recommend test runner for spec file modifications."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Edit",
            tool_input={"file_path": "/project/src/auth.spec.ts"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        recommendations = result.hook_outputs["pre_tool_use"]["recommendations"]
        assert any("test-writer-fixer" in r for r in recommendations)

    def test_recommends_secret_check_for_json_config(self):
        """Should recommend secret check for JSON config modifications."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Write",
            tool_input={"file_path": "/project/config.json"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        recommendations = result.hook_outputs["pre_tool_use"]["recommendations"]
        assert any("secrets" in r.lower() for r in recommendations)

    def test_recommends_secret_check_for_yaml_config(self):
        """Should recommend secret check for YAML config modifications."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Write",
            tool_input={"file_path": "/project/config.yaml"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        recommendations = result.hook_outputs["pre_tool_use"]["recommendations"]
        assert any("secrets" in r.lower() for r in recommendations)

    def test_no_recommendations_for_read(self):
        """Read operations should not generate recommendations."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "/project/src/auth.ts"},
        )
        hook = PreToolUseStateless()
        result = hook.process(ctx)

        recommendations = result.hook_outputs["pre_tool_use"]["recommendations"]
        assert len(recommendations) == 0


class TestPreToolUseJSONProtocol:
    """Test PreToolUseStateless through the full JSON protocol."""

    def test_json_protocol_safe_command(self):
        """Test full JSON protocol for a safe command."""
        input_json = json.dumps(
            {
                "session_id": "test_123",
                "tool_name": "Bash",
                "tool_input": {"command": "echo hello"},
            }
        )
        output = run_hook(PreToolUseStateless, input_json)
        data = json.loads(output)

        assert data["action"] == "continue"
        assert "context" in data

    def test_json_protocol_dangerous_command(self):
        """Test full JSON protocol for a dangerous command."""
        input_json = json.dumps(
            {
                "session_id": "test_123",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /"},
            }
        )
        output = run_hook(PreToolUseStateless, input_json)
        data = json.loads(output)

        assert data["action"] == "continue"  # JSON protocol wrapper always continues
        ctx = data["context"]
        hook_output = ctx["hook_outputs"]["pre_tool_use"]
        assert hook_output["action"] == "block"

    def test_json_protocol_sensitive_path(self):
        """Test full JSON protocol for sensitive file access."""
        input_json = json.dumps(
            {
                "session_id": "test_123",
                "tool_name": "Read",
                "tool_input": {"file_path": "/home/user/.ssh/id_rsa"},
            }
        )
        output = run_hook(PreToolUseStateless, input_json)
        data = json.loads(output)

        ctx = data["context"]
        hook_output = ctx["hook_outputs"]["pre_tool_use"]
        assert hook_output["action"] == "block"

    def test_json_protocol_minimal_input(self):
        """Test JSON protocol with minimal input."""
        input_json = json.dumps({"tool_name": "Read"})
        output = run_hook(PreToolUseStateless, input_json)
        data = json.loads(output)

        assert data["action"] == "continue"


# =============================================================================
# PostToolUseStateless Integration Tests
# =============================================================================


class TestPostToolUseFollowups:
    """Test PostToolUseStateless followup suggestions."""

    def test_suggests_code_review_for_write(self):
        """Write operations should suggest code review."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Write",
            tool_input={"file_path": "/project/src/auth.ts"},
        )
        hook = PostToolUseStateless()
        result = hook.process(ctx)

        followups = result.hook_outputs["post_tool_use"]["followups"]
        assert "suggest_code_review" in followups
        assert "check_for_tests" in followups

    def test_suggests_review_and_lint_for_edit(self):
        """Edit operations should suggest code review and linting."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Edit",
            tool_input={"file_path": "/project/src/index.ts"},
        )
        hook = PostToolUseStateless()
        result = hook.process(ctx)

        followups = result.hook_outputs["post_tool_use"]["followups"]
        assert "suggest_code_review" in followups
        assert "run_linter" in followups

    def test_suggests_validation_for_bash(self):
        """Bash operations should suggest output validation."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Bash",
            tool_input={"command": "npm install express"},
        )
        hook = PostToolUseStateless()
        result = hook.process(ctx)

        followups = result.hook_outputs["post_tool_use"]["followups"]
        assert "validate_output" in followups
        assert "check_side_effects" in followups

    def test_no_followups_for_read(self):
        """Read operations should have no followups."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "/project/src/index.ts"},
        )
        hook = PostToolUseStateless()
        result = hook.process(ctx)

        followups = result.hook_outputs["post_tool_use"]["followups"]
        assert len(followups) == 0

    def test_no_followups_for_glob(self):
        """Glob operations should have no followups."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Glob",
            tool_input={"pattern": "**/*.ts"},
        )
        hook = PostToolUseStateless()
        result = hook.process(ctx)

        followups = result.hook_outputs["post_tool_use"]["followups"]
        assert len(followups) == 0

    def test_no_followups_for_grep(self):
        """Grep operations should have no followups."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Grep",
            tool_input={"pattern": "TODO"},
        )
        hook = PostToolUseStateless()
        result = hook.process(ctx)

        followups = result.hook_outputs["post_tool_use"]["followups"]
        assert len(followups) == 0

    def test_empty_followups_for_unknown_tool(self):
        """Unknown tools should return empty followups list."""
        ctx = create_context(
            session_id="test_session",
            tool_name="UnknownTool",
            tool_input={},
        )
        hook = PostToolUseStateless()
        result = hook.process(ctx)

        followups = result.hook_outputs["post_tool_use"]["followups"]
        assert followups == []


class TestPostToolUseTruncation:
    """Test PostToolUseStateless truncation detection."""

    def test_no_warning_for_short_result(self):
        """Short results should not trigger truncation warning."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "test.py"},
        )
        ctx = update_context(ctx, tool_result="short content")

        hook = PostToolUseStateless()
        result = hook.process(ctx)

        warning = result.hook_outputs["post_tool_use"]["truncation_warning"]
        assert warning == ""

    def test_warning_for_large_result(self):
        """Large results should trigger truncation warning."""
        large_content = "x" * 60000
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "test.py"},
        )
        ctx = update_context(ctx, tool_result=large_content)

        hook = PostToolUseStateless()
        result = hook.process(ctx)

        warning = result.hook_outputs["post_tool_use"]["truncation_warning"]
        assert "truncated" in warning.lower()

    def test_no_warning_for_none_result(self):
        """None result should not trigger truncation warning."""
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "test.py"},
        )
        hook = PostToolUseStateless()
        result = hook.process(ctx)

        warning = result.hook_outputs["post_tool_use"]["truncation_warning"]
        assert warning == ""

    def test_no_warning_at_threshold_boundary(self):
        """Result at exactly the threshold should not trigger warning."""
        boundary_content = "x" * 50000
        ctx = create_context(
            session_id="test_session",
            tool_name="Read",
            tool_input={"file_path": "test.py"},
        )
        ctx = update_context(ctx, tool_result=boundary_content)

        hook = PostToolUseStateless()
        result = hook.process(ctx)

        warning = result.hook_outputs["post_tool_use"]["truncation_warning"]
        assert warning == ""


class TestPostToolUseJSONProtocol:
    """Test PostToolUseStateless through the full JSON protocol."""

    def test_json_protocol_write_operation(self):
        """Test full JSON protocol for Write operation."""
        input_json = json.dumps(
            {
                "session_id": "test_456",
                "tool_name": "Write",
                "tool_input": {"file_path": "/project/src/auth.ts"},
            }
        )
        output = run_hook(PostToolUseStateless, input_json)
        data = json.loads(output)

        assert data["action"] == "continue"
        ctx = data["context"]
        hook_output = ctx["hook_outputs"]["post_tool_use"]
        assert hook_output["action"] == "continue"
        assert "suggest_code_review" in hook_output["followups"]

    def test_json_protocol_read_operation(self):
        """Test full JSON protocol for Read operation."""
        input_json = json.dumps(
            {
                "session_id": "test_789",
                "tool_name": "Read",
                "tool_input": {"file_path": "/project/README.md"},
            }
        )
        output = run_hook(PostToolUseStateless, input_json)
        data = json.loads(output)

        assert data["action"] == "continue"
        ctx = data["context"]
        hook_output = ctx["hook_outputs"]["post_tool_use"]
        assert len(hook_output["followups"]) == 0


# =============================================================================
# Context Immutability Tests
# =============================================================================


class TestContextImmutability:
    """Test that hooks preserve context immutability."""

    def test_pre_tool_use_preserves_original_context(self):
        """PreToolUseStateless should not mutate original context."""
        ctx = create_context(
            session_id="immutable_test",
            tool_name="Bash",
            tool_input={"command": "ls"},
        )
        original_session_id = ctx.session_id
        original_tool_name = ctx.tool_name

        hook = PreToolUseStateless()
        result = hook.process(ctx)

        assert ctx.session_id == original_session_id
        assert ctx.tool_name == original_tool_name
        assert ctx.hook_outputs == {}
        assert result is not ctx
        assert "pre_tool_use" in result.hook_outputs

    def test_post_tool_use_preserves_original_context(self):
        """PostToolUseStateless should not mutate original context."""
        ctx = create_context(
            session_id="immutable_test",
            tool_name="Write",
            tool_input={"file_path": "test.py"},
        )
        original_hook_outputs = ctx.hook_outputs

        hook = PostToolUseStateless()
        result = hook.process(ctx)

        assert ctx.hook_outputs == original_hook_outputs
        assert result is not ctx
        assert "post_tool_use" in result.hook_outputs

    def test_chained_hooks_preserve_context(self):
        """Running both hooks in sequence should preserve all outputs."""
        ctx = create_context(
            session_id="chain_test",
            tool_name="Write",
            tool_input={"file_path": "/project/src/main.ts"},
        )

        pre_hook = PreToolUseStateless()
        after_pre = pre_hook.process(ctx)
        assert "pre_tool_use" in after_pre.hook_outputs

        post_hook = PostToolUseStateless()
        after_post = post_hook.process(after_pre)
        assert "post_tool_use" in after_post.hook_outputs
        assert "pre_tool_use" in after_post.hook_outputs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
