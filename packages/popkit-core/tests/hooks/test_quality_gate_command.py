#!/usr/bin/env python3
"""
Test quality-gate command normalization.
"""

from pathlib import Path
import importlib.util


def load_quality_gate_module():
    hook_path = Path(__file__).resolve().parents[2] / "hooks" / "quality-gate.py"
    spec = importlib.util.spec_from_file_location("quality_gate", hook_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_command_string():
    module = load_quality_gate_module()
    hook = module.QualityGateHook()
    cmd = hook.build_command("npx tsc --noEmit")
    assert cmd == ["npx", "tsc", "--noEmit"], f"Unexpected command: {cmd}"


def test_build_command_list():
    module = load_quality_gate_module()
    hook = module.QualityGateHook()
    cmd = hook.build_command(["npm", "run", "lint"])
    assert cmd == ["npm", "run", "lint"], f"Unexpected command: {cmd}"


if __name__ == "__main__":
    test_build_command_string()
    test_build_command_list()
    print("quality-gate command normalization tests passed")
