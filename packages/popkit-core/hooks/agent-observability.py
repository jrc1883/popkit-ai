#!/usr/bin/env python3
"""
PopKit Cloud Observability Hook

Sends agent telemetry data to PopKit Cloud for real-time monitoring
in the /observe dashboard.

Configuration:
  POPKIT_API_KEY  - Your PopKit API key (pk_live_... or pk_test_...)
  POPKIT_API_URL  - API endpoint (default: https://popkit-cloud-api.joseph-cannon.workers.dev)

Usage:
  Register as a PostToolUse hook in Claude Code:

  claude hooks add --event PostToolUse --command "python agent-observability.py"

  Or in .claude/settings.json:
  {
    "hooks": {
      "PostToolUse": ["python", "/path/to/agent-observability.py"]
    }
  }

For Pro tier users, events stream in real-time to the /observe dashboard.
Free tier users can still view events via polling.

Legacy Support:
  If OPTIMUS_WS_URL is set, also sends to local Optimus server for
  backward compatibility with existing Optimus Command Center setups.
"""

import json
import os
import sys
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# =============================================================================
# CONFIGURATION
# =============================================================================

# PopKit Cloud API
POPKIT_API_URL = os.environ.get(
    "POPKIT_API_URL", "https://popkit-cloud-api.joseph-cannon.workers.dev"
)
POPKIT_API_KEY = os.environ.get("POPKIT_API_KEY", "")

# Legacy Optimus support (optional)
OPTIMUS_WS_URL = os.environ.get("OPTIMUS_WS_URL", "")

# Event type mapping
EVENT_TYPE_MAP = {
    "PreToolUse": "tool_call",
    "PostToolUse": "tool_result",
    "AgentStart": "agent_start",
    "AgentEnd": "agent_end",
    "Error": "error",
    "post-tool-use": "tool_result",
    "agent-activation": "agent_start",
    "agent-collaboration": "workflow_phase",
}


# =============================================================================
# POPKIT CLOUD API
# =============================================================================


def send_to_popkit_cloud(event: dict) -> bool:
    """Send event to PopKit Cloud API.

    Args:
        event: Event data conforming to the /v1/events schema

    Returns:
        True if successful, False otherwise
    """
    if not POPKIT_API_KEY:
        return False

    try:
        url = f"{POPKIT_API_URL}/v1/events"
        headers = {
            "Authorization": f"Bearer {POPKIT_API_KEY}",
            "Content-Type": "application/json",
        }

        data = json.dumps(event).encode("utf-8")
        req = Request(url, data=data, headers=headers, method="POST")

        with urlopen(req, timeout=5) as response:
            return response.status == 201

    except (URLError, HTTPError):
        # Silent fail - don't disrupt Claude Code workflow
        return False
    except Exception:
        return False


# =============================================================================
# LEGACY OPTIMUS SUPPORT
# =============================================================================


def send_to_optimus(endpoint: str, data: dict) -> bool:
    """Send data to local Optimus server (legacy support).

    Only active if OPTIMUS_WS_URL environment variable is set.
    """
    if not OPTIMUS_WS_URL:
        return False

    try:
        import requests  # Optional dependency for legacy support

        response = requests.post(
            endpoint, json=data, timeout=2, headers={"Content-Type": "application/json"}
        )
        return response.status_code == 200
    except Exception:
        return False


# =============================================================================
# EVENT BUILDING
# =============================================================================


def build_cloud_event(data: dict) -> dict:
    """Build PopKit Cloud event from hook input.

    Args:
        data: Raw hook input data

    Returns:
        Event dict conforming to /v1/events schema
    """
    # Determine event type
    hook_event = data.get("hook_event", data.get("event_type", "PostToolUse"))
    event_type = EVENT_TYPE_MAP.get(hook_event, "tool_result")

    # Extract fields
    tool_name = data.get("tool_name", "")
    tool_result = data.get("tool_response", data.get("tool_result"))
    session_id = data.get("session_id", os.environ.get("CLAUDE_SESSION_ID", ""))

    # Agent info (Claude Code 2.0.64+)
    agent_id = data.get("agent_id", "")
    agent_type = data.get("agent_type", data.get("agent_name", ""))

    # Timing
    execution_time = data.get("execution_time", 0)
    duration = int(execution_time * 1000) if execution_time else None

    # Determine status
    status = "success"
    if tool_result:
        if isinstance(tool_result, dict):
            if tool_result.get("is_error") or tool_result.get("error"):
                status = "error"
        elif isinstance(tool_result, str) and "error" in tool_result.lower():
            status = "error"

    # Build event
    event = {
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": status,
    }

    if tool_name:
        event["toolName"] = tool_name
    if agent_id:
        event["agentId"] = agent_id
    if agent_type:
        event["agentType"] = agent_type
    if duration is not None:
        event["duration"] = duration
    if session_id:
        event["metadata"] = {
            "sessionId": session_id,
            "projectPath": os.getcwd(),
        }

    return event


def build_optimus_event(data: dict) -> dict:
    """Build Optimus-format event for legacy support."""
    return {
        "agentName": data.get(
            "agent_name", os.environ.get("CLAUDE_AGENT_NAME", "claude")
        ),
        "activity": f"tool_use:{data.get('tool_name', '')}",
        "metadata": {
            "toolName": data.get("tool_name", ""),
            "toolArgs": data.get("tool_input", data.get("tool_args", {})),
            "executionTime": data.get("execution_time", 0),
            "success": data.get("tool_result") is not None,
            "sessionId": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "projectPath": os.getcwd(),
        },
    }


# =============================================================================
# MAIN HOOK ENTRY POINT
# =============================================================================


def main():
    """Main hook entry point - JSON stdin/stdout protocol."""
    try:
        # Read JSON input from stdin
        input_data = sys.stdin.read()
        data = json.loads(input_data) if input_data.strip() else {}

        # Send to PopKit Cloud (primary)
        cloud_event = build_cloud_event(data)
        cloud_sent = send_to_popkit_cloud(cloud_event)

        # Send to Optimus (legacy, if configured)
        optimus_sent = False
        if OPTIMUS_WS_URL and data.get("tool_name"):
            optimus_event = build_optimus_event(data)
            optimus_sent = send_to_optimus(
                f"{OPTIMUS_WS_URL}/api/agent/activity", optimus_event
            )

        # Output JSON response (Claude Code hook protocol)
        response = {
            "action": "continue",
            "status": "success",
            "cloud_sent": cloud_sent,
            "optimus_sent": optimus_sent,
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))

    except json.JSONDecodeError as e:
        response = {
            "action": "continue",
            "status": "error",
            "error": f"Invalid JSON: {e}",
        }
        print(json.dumps(response))
    except Exception as e:
        response = {"action": "continue", "status": "error", "error": str(e)}
        print(json.dumps(response))


if __name__ == "__main__":
    main()
