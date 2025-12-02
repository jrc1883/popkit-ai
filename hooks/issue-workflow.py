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
from flag_parser import parse_work_args


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
            phases = config.get("suggested_phases", [])
            power_state = {
                "active": True,
                "activated_at": datetime.now().isoformat(),
                "source": f"issue #{config.get('issue_number', 'unknown')}",
                "active_issue": config.get("issue_number"),
                "session_id": f"pop-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                # Status line fields
                "current_phase": phases[0] if phases else "implementation",
                "phase_index": 1,
                "total_phases": len(phases) if phases else 1,
                "progress": 0.0,
                "phases_completed": [],
                # Config for reference
                "config": {
                    "phases": phases,
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

    def start_work_on_issue(self, issue_number: int, flags: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start working on an issue with flag support - for /popkit:work command.

        This is the enhanced version of start_issue_workflow that respects
        command-line flags for Power Mode control.

        Args:
            issue_number: The issue number to work on
            flags: Dict from parse_work_args with:
                - force_power: bool - Force Power Mode ON
                - force_solo: bool - Force Power Mode OFF
                - phases: List[str] - Override phases
                - agents: List[str] - Override agents

        Returns:
            Dict with workflow configuration and actions to take
        """
        flags = flags or {}

        result = {
            "success": False,
            "issue_number": issue_number,
            "workflow": None,
            "power_mode": False,
            "power_mode_source": None,
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

        # Override phases if specified
        if flags.get("phases"):
            workflow["suggested_phases"] = flags["phases"]
            result["messages"].append(f"Using custom phases: {', '.join(flags['phases'])}")

        # Override agents if specified
        if flags.get("agents"):
            workflow["config"]["agents"] = {
                "primary": flags["agents"][:1] if flags["agents"] else [],
                "supporting": flags["agents"][1:] if len(flags["agents"]) > 1 else []
            }
            result["messages"].append(f"Using custom agents: {', '.join(flags['agents'])}")

        # Determine Power Mode activation (flag priority)
        should_activate_power = False
        power_source = "none"

        if flags.get("force_power"):
            # Flag -p or --power takes highest priority
            should_activate_power = True
            power_source = "flag (-p/--power)"
        elif flags.get("force_solo"):
            # Flag --solo forces sequential mode
            should_activate_power = False
            power_source = "flag (--solo)"
        elif workflow.get("should_activate_power_mode"):
            # Use PopKit Guidance recommendation
            should_activate_power = True
            config = workflow.get("config", {})
            power_source = f"PopKit Guidance (power_mode: {config.get('power_mode')}, complexity: {config.get('complexity')})"
        else:
            # Default to sequential
            should_activate_power = False
            power_source = "default (sequential)"

        result["power_mode"] = should_activate_power
        result["power_mode_source"] = power_source

        # Determine actions
        if workflow.get("should_brainstorm"):
            result["actions"].append({
                "type": "trigger_skill",
                "skill": "pop-brainstorming",
                "reason": "Issue specifies 'Brainstorm First' workflow"
            })
            result["messages"].append("Brainstorming recommended before implementation")

        if should_activate_power:
            result["actions"].append({
                "type": "activate_power_mode",
                "reason": power_source
            })
            self.activate_power_mode({
                "issue_number": issue_number,
                **workflow
            })
            result["messages"].append(f"Power Mode activated ({power_source})")
        else:
            result["messages"].append(f"Sequential mode ({power_source})")

        # Generate todos from phases
        result["todos"] = self.generate_todo_list(workflow)

        # Update state
        self.state["active_issue"] = issue_number
        self.state["current_phase"] = workflow.get("suggested_phases", ["implementation"])[0]
        self.state["phases_completed"] = []
        self.state["activated_at"] = datetime.now().isoformat()
        self.state["power_mode"] = should_activate_power
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

            for i, phase in enumerate(phases):
                if phase not in completed:
                    result["next_phase"] = phase
                    self.state["current_phase"] = phase
                    # Update power mode state for status line
                    self._update_power_mode_progress(
                        current_phase=phase,
                        phase_index=i + 1,
                        total_phases=len(phases),
                        phases_completed=list(completed)
                    )
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

    def _update_power_mode_progress(
        self,
        current_phase: str,
        phase_index: int,
        total_phases: int,
        phases_completed: List[str]
    ):
        """Update power mode state file for status line integration."""
        try:
            if self.power_mode_state.exists():
                power_state = json.loads(self.power_mode_state.read_text())
                if power_state.get("active"):
                    power_state["current_phase"] = current_phase
                    power_state["phase_index"] = phase_index
                    power_state["total_phases"] = total_phases
                    power_state["phases_completed"] = phases_completed
                    # Calculate progress as percentage of phases complete
                    power_state["progress"] = len(phases_completed) / total_phases if total_phases > 0 else 0.0
                    self.power_mode_state.write_text(json.dumps(power_state, indent=2))
        except Exception:
            pass  # Don't fail if status update fails

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

        elif action == "work":
            # Enhanced version with flag support (for /popkit:work command)
            args = input_data.get("args", "")
            flags = parse_work_args(args)

            if flags.get("error"):
                print(json.dumps({"error": flags["error"]}))
                sys.exit(1)

            issue_number = flags.get("issue_number")
            if not issue_number:
                print(json.dumps({"error": "issue_number required"}))
                sys.exit(1)

            result = hook.start_work_on_issue(issue_number, flags)

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

        elif sys.argv[1] == "work" and len(sys.argv) > 2:
            # Enhanced version with flag support
            # Usage: python issue-workflow.py work "#4 -p"
            args = " ".join(sys.argv[2:])
            flags = parse_work_args(args)

            if flags.get("error"):
                print(json.dumps({"error": flags["error"]}, indent=2))
                sys.exit(1)

            hook = IssueWorkflowHook()
            result = hook.start_work_on_issue(flags["issue_number"], flags)
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
            print("  python issue-workflow.py work #4 -p            # Start with flags (Power Mode)")
            print("  python issue-workflow.py work #4 --solo        # Start without Power Mode")
            print("  python issue-workflow.py status                # Get current status")
            print("  python issue-workflow.py complete <phase>      # Complete a phase")
    else:
        main()
