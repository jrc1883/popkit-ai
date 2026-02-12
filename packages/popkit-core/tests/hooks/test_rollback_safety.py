#!/usr/bin/env python3
"""
Test that destructive rollback is gated behind explicit opt-in.
"""

from pathlib import Path
import importlib.util


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_quality_gate_guard():
    hook_path = Path(__file__).resolve().parents[2] / "hooks" / "quality-gate.py"
    module = load_module("quality_gate", hook_path)
    hook = module.QualityGateHook()
    assert hook.destructive_ops_allowed() is False, (
        "Destructive ops should be disabled by default"
    )


def test_issue_workflow_guard():
    hook_path = Path(__file__).resolve().parents[2] / "hooks" / "issue-workflow.py"
    module = load_module("issue_workflow", hook_path)
    hook = module.IssueWorkflowHook()
    assert hook.destructive_ops_allowed() is False, (
        "Destructive ops should be disabled by default"
    )
    result = hook.rollback_to_phase_start("implementation")
    assert result["success"] is False
    assert "Rollback blocked" in result["message"]


if __name__ == "__main__":
    test_quality_gate_guard()
    test_issue_workflow_guard()
    print("rollback safety guard tests passed")
