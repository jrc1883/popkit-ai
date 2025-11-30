#!/usr/bin/env python3
"""
Issue Workflow Hook - Activation Logic for Issue-Driven Development

Integrates with /popkit:issue work <number> to:
1. Fetch and parse issue with PopKit Guidance section
2. Determine if brainstorming should be triggered
3. Determine if Power Mode should activate
4. Create todos from phases
5. Suggest agents based on issue type and guidance

This hook ties together:
- Issue Parser (github_issues.py)
- Quality Gates (quality-gate.py)
- Power Mode (power-mode/)

Part of Issue #11 - Unified Orchestration System
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from github_issues import (
    get_workflow_config,
    infer_issue_type,
    get_agents_for_issue_type
)


class IssueWorkflowHook:
    """Manages issue-driven workflow activation."""

    def __init__(self):
        self.cwd = Path.cwd()
        self.claude_dir = self.cwd / ".claude"
        self.state_file = self.claude_dir / "issue-workflow-state.json"
        self.power_mode_state = self.claude_dir / "power-mode-state.json"

        # Ensure directory exists
        self.claude_dir.mkdir(exist_ok=True)

        # Load state
        self.state = self.load_state()

    def load_state(self) -> Dict[str, Any]:
        """Load workflow state from file."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except json.JSONDecodeError:
                pass
        return {
            "active_issue": None,
            "current_phase": None,
            "phases_completed": [],
            "activated_at": None
        }

    def save_state(self):
        """Persist workflow state to file."""
        try:
            self.state_file.write_text(json.dumps(self.state, indent=2))
        except Exception as e:
            print(f"Warning: Could not save state: {e}", file=sys.stderr)

    def activate_power_mode(self, config: Dict[str, Any]) -> bool:
        """Activate Power Mode with configuration from issue."""
        try:
            power_state = {
                "active": True,
                "activated_at": datetime.now().isoformat(),
                "source": f"issue #{config.get('issue_number', 'unknown')}",
                "config": {
                    "phases": config.get("suggested_phases", []),
                    "agents": config.get("config", {}).get("agents", {}),
                    "quality_gates": config.get("config", {}).get("quality_gates", [])
                }
            }
            self.power_mode_state.write_text(json.dumps(power_state, indent=2))
            return True
        except Exception as e:
            print(f"Warning: Could not activate Power Mode: {e}", file=sys.stderr)
            return False

    def deactivate_power_mode(self):
        """Deactivate Power Mode."""
        try:
            if self.power_mode_state.exists():
                power_state = json.loads(self.power_mode_state.read_text())
                power_state["active"] = False
                power_state["deactivated_at"] = datetime.now().isoformat()
                self.power_mode_state.write_text(json.dumps(power_state, indent=2))
        except Exception:
            pass

    def generate_todo_list(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate todo list from issue phases and configuration."""
        todos = []
        phases = config.get("suggested_phases", [])

        phase_descriptions = {
            "discovery": "Research and gather context for the issue",
            "architecture": "Design the solution architecture",
            "implementation": "Implement the solution",
            "testing": "Write and run tests",
            "documentation": "Update documentation",
            "review": "Review and finalize changes"
        }

        for i, phase in enumerate(phases):
            todos.append({
                "content": f"Phase {i+1}: {phase.title()} - {phase_descriptions.get(phase, phase)}",
                "status": "pending" if i > 0 else "in_progress",
                "activeForm": f"Working on {phase}"
            })

        return todos

    def format_workflow_summary(self, workflow: Dict[str, Any]) -> str:
        """Format workflow configuration as readable summary."""
        issue = workflow.get("issue", {})
        config = workflow.get("config", {})

        lines = [
            "",
            "=" * 60,
            f"Issue #{issue.get('number')}: {issue.get('title', 'Unknown')}",
            "=" * 60,
            "",
            f"State: {issue.get('state', 'Unknown')}",
            f"Labels: {', '.join(issue.get('labels', []))}",
            "",
            "Workflow Configuration:",
            f"  Type: {config.get('workflow_type', 'direct')}",
            f"  Complexity: {config.get('complexity', 'medium')}",
            f"  Power Mode: {config.get('power_mode', 'not_needed')}",
            "",
            "Phases:",
        ]

        for phase in workflow.get("suggested_phases", []):
            lines.append(f"  - {phase}")

        lines.extend([
            "",
            "Agents:",
            f"  Primary: {', '.join(config.get('agents', {}).get('primary', ['none']))}",
            f"  Supporting: {', '.join(config.get('agents', {}).get('supporting', ['none']))}",
            "",
            "Quality Gates:",
        ])

        for gate in config.get("quality_gates", []):
            lines.append(f"  - {gate}")

        lines.extend([
            "",
            "-" * 60,
            "Activation:",
            f"  Should Brainstorm: {'Yes' if workflow.get('should_brainstorm') else 'No'}",
            f"  Should Activate Power Mode: {'Yes' if workflow.get('should_activate_power_mode') else 'No'}",
            "-" * 60,
            ""
        ])

        return '\n'.join(lines)

    def start_issue_workflow(self, issue_number: int) -> Dict[str, Any]:
        """Start working on an issue - main entry point.

        Args:
            issue_number: The issue number to work on

        Returns:
            Dict with workflow configuration and actions to take
        """
        result = {
            "success": False,
            "issue_number": issue_number,
            "workflow": None,
            "actions": [],
            "todos": [],
            "messages": []
        }

        # Fetch and parse issue
        workflow = get_workflow_config(issue_number)

        if workflow.get("error"):
            result["messages"].append(f"Error: {workflow['error']}")
            return result

        result["workflow"] = workflow
        result["success"] = True

        # Determine actions
        if workflow.get("should_brainstorm"):
            result["actions"].append({
                "type": "trigger_skill",
                "skill": "pop-brainstorming",
                "reason": "Issue specifies 'Brainstorm First' workflow"
            })
            result["messages"].append("Brainstorming recommended before implementation")

        if workflow.get("should_activate_power_mode"):
            result["actions"].append({
                "type": "activate_power_mode",
                "reason": f"Power Mode: {workflow['config']['power_mode']}, Complexity: {workflow['config']['complexity']}"
            })
            self.activate_power_mode({
                "issue_number": issue_number,
                **workflow
            })
            result["messages"].append("Power Mode activated for parallel agent coordination")

        # Generate todos from phases
        result["todos"] = self.generate_todo_list(workflow)

        # Update state
        self.state["active_issue"] = issue_number
        self.state["current_phase"] = workflow.get("suggested_phases", ["implementation"])[0]
        self.state["phases_completed"] = []
        self.state["activated_at"] = datetime.now().isoformat()
        self.save_state()

        # Add summary message
        result["messages"].append(self.format_workflow_summary(workflow))

        return result

    def complete_phase(self, phase_name: str) -> Dict[str, Any]:
        """Mark a phase as complete and determine next steps.

        Args:
            phase_name: Name of the phase to complete

        Returns:
            Dict with next phase and any actions to take
        """
        result = {
            "completed": phase_name,
            "next_phase": None,
            "actions": [],
            "messages": []
        }

        # Load current workflow state
        if not self.state.get("active_issue"):
            result["messages"].append("No active issue workflow")
            return result

        # Mark phase complete
        if phase_name not in self.state.get("phases_completed", []):
            self.state["phases_completed"].append(phase_name)

        # Determine next phase
        workflow = get_workflow_config(self.state["active_issue"])
        if workflow.get("error"):
            result["messages"].append(f"Warning: Could not fetch issue: {workflow['error']}")
        else:
            phases = workflow.get("suggested_phases", [])
            completed = set(self.state.get("phases_completed", []))

            for phase in phases:
                if phase not in completed:
                    result["next_phase"] = phase
                    self.state["current_phase"] = phase
                    break

            if not result["next_phase"]:
                result["messages"].append("All phases complete!")
                result["actions"].append({
                    "type": "deactivate_power_mode",
                    "reason": "All phases complete"
                })
                self.deactivate_power_mode()

        self.save_state()
        return result

    def get_current_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        if not self.state.get("active_issue"):
            return {"active": False, "message": "No active issue workflow"}

        workflow = get_workflow_config(self.state["active_issue"])

        return {
            "active": True,
            "issue_number": self.state["active_issue"],
            "current_phase": self.state.get("current_phase"),
            "phases_completed": self.state.get("phases_completed", []),
            "phases_remaining": [
                p for p in workflow.get("suggested_phases", [])
                if p not in self.state.get("phases_completed", [])
            ],
            "activated_at": self.state.get("activated_at")
        }


def main():
    """Main entry point - JSON stdin/stdout protocol."""
    try:
        input_data = json.loads(sys.stdin.read())
        hook = IssueWorkflowHook()

        action = input_data.get("action", "status")

        if action == "start":
            issue_number = input_data.get("issue_number")
            if not issue_number:
                print(json.dumps({"error": "issue_number required"}))
                sys.exit(1)
            result = hook.start_issue_workflow(issue_number)

        elif action == "complete_phase":
            phase_name = input_data.get("phase_name")
            if not phase_name:
                print(json.dumps({"error": "phase_name required"}))
                sys.exit(1)
            result = hook.complete_phase(phase_name)

        elif action == "status":
            result = hook.get_current_status()

        else:
            result = {"error": f"Unknown action: {action}"}

        print(json.dumps(result))

    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(0)


if __name__ == "__main__":
    # CLI mode for testing
    if len(sys.argv) > 1:
        if sys.argv[1] == "start" and len(sys.argv) > 2:
            issue_num = int(sys.argv[2])
            hook = IssueWorkflowHook()
            result = hook.start_issue_workflow(issue_num)
            print(json.dumps(result, indent=2))

        elif sys.argv[1] == "status":
            hook = IssueWorkflowHook()
            result = hook.get_current_status()
            print(json.dumps(result, indent=2))

        elif sys.argv[1] == "complete" and len(sys.argv) > 2:
            phase = sys.argv[2]
            hook = IssueWorkflowHook()
            result = hook.complete_phase(phase)
            print(json.dumps(result, indent=2))

        else:
            print("Usage:")
            print("  python issue-workflow.py start <issue_number>  # Start working on issue")
            print("  python issue-workflow.py status                # Get current status")
            print("  python issue-workflow.py complete <phase>      # Complete a phase")
    else:
        main()
