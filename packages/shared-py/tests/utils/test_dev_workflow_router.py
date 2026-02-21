"""Tests for dev_workflow_router.py (Issue #218)."""

import json

from popkit_shared.utils.dev_provider_resolver import DevProvider
from popkit_shared.utils.dev_workflow_router import (
    DevWorkflowRequest,
    DevWorkflowRouter,
    format_plan_display,
    main,
)


def test_build_plan_auto_prefers_feature_dev_for_commodity_paths():
    router = DevWorkflowRouter()
    request = DevWorkflowRequest(
        task="add auth flow",
        requested_provider=DevProvider.AUTO,
        requires_popkit_orchestration=False,
        requires_github_cache=False,
    )
    plugins = [{"name": "feature-dev"}]

    plan = router.build_plan(request, plugin_scan_data=plugins)

    assert plan.execution_mode == "delegated"
    assert plan.primary_command == "/popkit:feature-dev"
    assert plan.fallback_command is not None
    assert "--provider popkit" in plan.fallback_command
    assert plan.decision.selected_provider == DevProvider.FEATURE_DEV


def test_build_plan_auto_forces_popkit_when_popkit_capability_required():
    router = DevWorkflowRouter()
    request = DevWorkflowRequest(
        task="complex orchestration",
        requested_provider=DevProvider.AUTO,
        requires_popkit_orchestration=True,
    )
    plugins = [{"name": "feature-dev"}]

    plan = router.build_plan(request, plugin_scan_data=plugins)

    assert plan.execution_mode == "native"
    assert plan.primary_command.startswith("/popkit-dev:dev")
    assert "--provider popkit" in plan.primary_command
    assert plan.decision.selected_provider == DevProvider.POPKIT


def test_build_plan_explicit_feature_dev_falls_back_when_unavailable():
    router = DevWorkflowRouter()
    request = DevWorkflowRequest(
        task="add telemetry",
        requested_provider=DevProvider.FEATURE_DEV,
    )

    plan = router.build_plan(request, plugin_scan_data=[])

    assert plan.execution_mode == "native"
    assert plan.primary_command.startswith("/popkit-dev:dev")
    assert any(
        "feature-dev was requested but unavailable" in reason for reason in plan.decision.rationale
    )
    assert plan.decision.selected_provider == DevProvider.POPKIT


def test_build_plan_uses_issue_work_target_when_issue_number_provided():
    router = DevWorkflowRouter()
    request = DevWorkflowRequest(
        task="",
        issue_number=218,
        requested_provider=DevProvider.POPKIT,
    )

    plan = router.build_plan(request, plugin_scan_data=[])

    assert plan.primary_command.startswith("/popkit-dev:dev work #218")
    assert "--mode full" in plan.primary_command
    assert "--provider popkit" in plan.primary_command


def test_build_plan_normalizes_invalid_mode_to_full():
    router = DevWorkflowRouter()
    request = DevWorkflowRequest(
        task="stabilize ci",
        mode="turbo",
        requested_provider=DevProvider.POPKIT,
    )

    plan = router.build_plan(request, plugin_scan_data=[])

    assert "--mode full" in plan.primary_command


def test_format_plan_display_includes_fallback_for_delegated_plan():
    router = DevWorkflowRouter()
    request = DevWorkflowRequest(task="add auth", requested_provider=DevProvider.AUTO)
    plan = router.build_plan(request, plugin_scan_data=[{"name": "feature-dev"}])

    output = format_plan_display(plan)

    assert "Selected provider: feature-dev" in output
    assert "Primary command: /popkit:feature-dev" in output
    assert "Fallback command:" in output


def test_main_json_output_uses_plugins_json_file(tmp_path, capsys):
    plugins_file = tmp_path / "plugins.json"
    plugins_file.write_text('[{"name":"feature-dev"}]', encoding="utf-8")

    exit_code = main(
        [
            "--task",
            "add telemetry",
            "--provider",
            "auto",
            "--plugins-json",
            str(plugins_file),
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["decision"]["selected_provider"] == "feature-dev"


def test_main_returns_error_for_invalid_plugins_json(tmp_path, capsys):
    plugins_file = tmp_path / "bad-plugins.json"
    plugins_file.write_text("{", encoding="utf-8")

    exit_code = main(["--task", "fix auth", "--plugins-json", str(plugins_file)])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Failed to load plugins JSON" in captured.err
