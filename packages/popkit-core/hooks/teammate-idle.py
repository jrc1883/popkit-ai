#!/usr/bin/env python3
"""
NATIVE SWARM AUTO-DRIVE HOOK

This hook implements automatic task claiming for idle teammates in a Native Swarm.
When a teammate is detected as idle, this hook injects instructions to:
1. Check TaskList for unassigned tasks
2. Claim tasks matching their role
3. Report status to the Team Lead if no tasks available

This removes "manager latency" by enabling self-organizing behavior.
"""

import sys
import json
import os
from datetime import datetime

# Role-to-task matching heuristics
ROLE_KEYWORDS = {
    "Engineer": [
        "implement",
        "code",
        "build",
        "fix",
        "develop",
        "create",
        "write code",
    ],
    "Researcher": ["research", "investigate", "analyze", "explore", "find", "discover"],
    "Architect": ["design", "architect", "structure", "plan", "system"],
    "Tester": ["test", "verify", "validate", "check", "qa", "quality"],
    "Security Auditor": [
        "security",
        "audit",
        "vulnerability",
        "scan",
        "review security",
    ],
    "Documentation": ["document", "docs", "readme", "write doc", "update doc"],
}


def detect_role_from_context(input_data):
    """
    Attempt to detect the teammate's role from context.
    Returns the most likely role or 'General' if unknown.
    """
    teammate_id = input_data.get("teammateId", "")
    teammate_name = input_data.get("teammateName", "")
    agent_type = input_data.get("agentType", "")

    # Check if role is explicitly provided
    if "role" in input_data:
        return input_data["role"]

    # Infer from agent type or name
    combined = f"{teammate_id} {teammate_name} {agent_type}".lower()

    for role, keywords in ROLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in combined:
                return role

    return "General"


def build_auto_claim_instruction(role, teammate_id):
    """
    Build the instruction prompt that will be injected into the idle agent's context.
    This prompt guides the agent to self-organize by claiming appropriate tasks.
    """
    instruction_parts = [
        f"🔔 AUTO-DRIVE ACTIVATED | Teammate: {teammate_id} | Role: {role}",
        "",
        "You are currently IDLE in a Native Swarm team session.",
        "",
        "IMMEDIATE ACTIONS REQUIRED:",
        "",
        "1. **Check Task Board**: Call `TaskList` to see all available tasks.",
        "",
        "2. **Claim Matching Task**: Look for tasks that match your role:",
    ]

    # Add role-specific guidance
    if role in ROLE_KEYWORDS:
        keywords = ROLE_KEYWORDS[role]
        instruction_parts.append(
            f"   - Keywords to look for: {', '.join(keywords[:3])}"
        )

    instruction_parts.extend(
        [
            "",
            "3. **Claim Process**:",
            "   ```",
            f'   TaskUpdate(task_id="<id>", status="IN_PROGRESS", notes="Claimed by {role}")',
            "   ```",
            "",
            "4. **If No Tasks Available**:",
            "   - Report to Team Lead: `SendMessage(recipient='TeamLead', message='No matching tasks. Awaiting assignment.')`",
            "",
            "5. **If Task Requires Sandbox**:",
            "   - Check if sandbox_id is mentioned in task description",
            "   - Use provided sandbox for file operations",
            "   - Request sandbox from Team Lead if needed but not provided",
            "",
            "PRIORITY: Claim the FIRST matching task to maximize throughput.",
            "",
            f"Timestamp: {datetime.utcnow().isoformat()}Z",
        ]
    )

    return "\n".join(instruction_parts)


def log_idle_event(input_data, role):
    """
    Log idle events for observability (optional).
    Writes to .claude/popkit/swarm-events.jsonl if the directory exists.
    """
    try:
        log_dir = os.path.expanduser("~/.claude/popkit")
        if os.path.exists(log_dir):
            log_file = os.path.join(log_dir, "swarm-events.jsonl")
            event = {
                "event": "teammate_idle",
                "teammate_id": input_data.get("teammateId"),
                "role": role,
                "timestamp": datetime.utcnow().isoformat(),
                "action": "auto_drive_triggered",
            }
            with open(log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
    except Exception:
        pass  # Logging is optional, don't fail the hook


def main():
    """
    Main hook handler for TeammateIdle event.

    Reads context from stdin (JSON), determines appropriate action,
    and outputs instruction to be injected into the idle agent's context.
    """
    # 1. Read context passed by Claude
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        input_data = {}

    # 2. Detect teammate role
    teammate_id = input_data.get("teammateId", "unknown")
    role = detect_role_from_context(input_data)

    # 3. Check if we're in swarm mode (optional check)
    # If not in swarm mode, we could skip or provide minimal instruction
    in_swarm = input_data.get("inSwarmMode", True)  # Default to True for Native Swarm

    if not in_swarm:
        # Not in swarm mode, provide minimal guidance
        print(
            json.dumps(
                {
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": "system",
                    "content": "You appear to be idle. Continue with your assigned task or ask the user for next steps.",
                }
            )
        )
        return

    # 4. Build and output the auto-claim instruction
    instruction = build_auto_claim_instruction(role, teammate_id)

    # 5. Log the event (optional)
    log_idle_event(input_data, role)

    # 6. Output the instruction as system message with required fields
    # This gets injected into the idle agent's context
    print(
        json.dumps(
            {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "role": "system",
                "content": instruction,
            }
        )
    )


if __name__ == "__main__":
    main()
