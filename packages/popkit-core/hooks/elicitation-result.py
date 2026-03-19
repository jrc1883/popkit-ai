#!/usr/bin/env python3
"""
ElicitationResult Hook (Claude Code 2.1.76+)
Fires when the user responds to an elicitation (structured input dialog).

Captures elicitation responses for PopKit's state management, persisting
key decisions so they survive context compaction and are available to
future hooks and agents.

Responsibilities:
1. Read the elicitation result from stdin JSON
2. Detect if it contains a key decision (deploy target, architecture choice, etc.)
3. Persist decisions to:
   - .claude/STATUS.json context.keyDecisions
   - .claude/popkit/decisions-log.json
4. Lightweight (< 2 seconds), stdlib only
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def _get_plugin_data_dir() -> Path:
    """Get plugin data directory (CLAUDE_PLUGIN_DATA or fallback)."""
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return Path(plugin_data)
    return Path.cwd() / ".claude" / "popkit"


# Decision categories and their detection signals
DECISION_CATEGORIES = {
    "deploy": {
        "signals": [
            "deploy",
            "target",
            "environment",
            "staging",
            "production",
            "release",
            "rollout",
        ],
        "label": "Deployment",
    },
    "architecture": {
        "signals": [
            "architect",
            "design",
            "pattern",
            "structure",
            "approach",
            "framework",
            "stack",
            "database",
            "api",
        ],
        "label": "Architecture",
    },
    "configuration": {
        "signals": [
            "config",
            "setting",
            "option",
            "preference",
            "parameter",
            "threshold",
            "limit",
        ],
        "label": "Configuration",
    },
    "workflow": {
        "signals": [
            "workflow",
            "process",
            "pipeline",
            "automation",
            "ci",
            "branch",
            "merge",
            "strategy",
        ],
        "label": "Workflow",
    },
    "scope": {
        "signals": [
            "scope",
            "feature",
            "priority",
            "include",
            "exclude",
            "requirement",
            "acceptance",
        ],
        "label": "Scope",
    },
}


def classify_decision(result_data):
    """Classify an elicitation result into a decision category.

    Examines the original elicitation message and the user's response
    to determine if this constitutes a key decision worth persisting.

    Args:
        result_data: Dict from stdin with elicitation result details

    Returns:
        Tuple of (category_key, category_label) or (None, None)
    """
    # Combine relevant text fields for signal matching
    message = result_data.get("message", "").lower()
    title = result_data.get("title", "").lower()
    response_text = ""

    # Extract text from the response value
    response = result_data.get("response", result_data.get("value", ""))
    if isinstance(response, str):
        response_text = response.lower()
    elif isinstance(response, dict):
        response_text = json.dumps(response).lower()
    elif isinstance(response, list):
        response_text = " ".join(str(item) for item in response).lower()

    combined = f"{message} {title} {response_text}"

    # Score each category
    best_category = None
    best_score = 0

    for cat_key, cat_info in DECISION_CATEGORIES.items():
        score = sum(1 for signal in cat_info["signals"] if signal in combined)
        if score > best_score:
            best_score = score
            best_category = cat_key

    # Require at least 1 signal match to count as a decision
    if best_score >= 1 and best_category:
        return best_category, DECISION_CATEGORIES[best_category]["label"]

    return None, None


def build_decision_entry(result_data, category, label):
    """Build a structured decision entry from the elicitation result.

    Args:
        result_data: Dict from stdin with elicitation result details
        category: Decision category key (e.g., 'deploy')
        label: Human-readable category label (e.g., 'Deployment')

    Returns:
        Dict representing the decision entry
    """
    # Extract the response value
    response = result_data.get("response", result_data.get("value", ""))

    # Build a concise summary
    message = result_data.get("message", result_data.get("title", ""))
    if isinstance(response, str):
        summary = f"{message}: {response}" if message else response
    elif isinstance(response, dict):
        # For structured responses, pick key fields
        summary_parts = []
        if message:
            summary_parts.append(message)
        for key, val in response.items():
            if val and str(val).strip():
                summary_parts.append(f"{key}={val}")
        summary = " | ".join(summary_parts) if summary_parts else json.dumps(response)
    else:
        summary = f"{message}: {response}" if message else str(response)

    # Truncate long summaries
    if len(summary) > 200:
        summary = summary[:197] + "..."

    return {
        "category": category,
        "label": label,
        "summary": summary,
        "response": response,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }


def persist_to_status_json(decision_entry):
    """Persist a decision to STATUS.json under context.keyDecisions.

    Merges into the existing STATUS.json without overwriting other fields.

    Args:
        decision_entry: Dict with the decision details
    """
    status_file = Path.cwd() / ".claude" / "STATUS.json"

    status = {}
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
        except (json.JSONDecodeError, OSError):
            status = {}

    # Ensure context.keyDecisions exists
    if "context" not in status:
        status["context"] = {}
    if "keyDecisions" not in status["context"]:
        status["context"]["keyDecisions"] = []

    # Append the decision
    status["context"]["keyDecisions"].append(decision_entry)

    # Keep only the last 50 decisions in STATUS.json (it should stay compact)
    if len(status["context"]["keyDecisions"]) > 50:
        status["context"]["keyDecisions"] = status["context"]["keyDecisions"][-50:]

    status["lastUpdate"] = datetime.now().isoformat() + "Z"

    try:
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
    except OSError as e:
        print(f"  Warning: failed to update STATUS.json: {e}", file=sys.stderr)


def persist_to_decisions_log(decision_entry):
    """Persist a decision to the long-term decisions log.

    This is the full audit trail of all decisions, kept separately from
    STATUS.json which is meant to be compact.
    Uses CLAUDE_PLUGIN_DATA (CC 2.1.78+) or falls back to .claude/popkit/.

    Args:
        decision_entry: Dict with the decision details
    """
    log_file = _get_plugin_data_dir() / "decisions-log.json"

    log_entries = []
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_entries = json.load(f)
        except (json.JSONDecodeError, OSError):
            log_entries = []

    log_entries.append(decision_entry)

    # Keep last 200 entries in the log
    if len(log_entries) > 200:
        log_entries = log_entries[-200:]

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_entries, f, indent=2)
    except OSError as e:
        print(f"  Warning: failed to write decisions log: {e}", file=sys.stderr)


def process_elicitation_result(result_data):
    """Process an elicitation result and persist key decisions.

    Args:
        result_data: Dict from stdin containing the elicitation result

    Returns:
        Dict with the hook response
    """
    category, label = classify_decision(result_data)

    if category is None:
        # Not a key decision -- nothing to persist
        return {
            "status": "success",
            "message": "Elicitation result processed (no key decision detected)",
            "timestamp": datetime.now().isoformat(),
        }

    # Build and persist the decision entry
    decision_entry = build_decision_entry(result_data, category, label)

    persist_to_status_json(decision_entry)
    persist_to_decisions_log(decision_entry)

    print(
        f"  Decision persisted [{label}]: {decision_entry['summary'][:80]}",
        file=sys.stderr,
    )

    return {
        "status": "success",
        "message": f"Key decision persisted: {label}",
        "decision": decision_entry,
        "timestamp": datetime.now().isoformat(),
    }


def main():
    """Main entry point - JSON stdin/stdout protocol."""
    try:
        input_data = sys.stdin.read()
        data = json.loads(input_data) if input_data.strip() else {}

        result = process_elicitation_result(data)

        print(json.dumps(result))

    except json.JSONDecodeError:
        response = {
            "status": "success",
            "message": "ElicitationResult hook completed (no input)",
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
    except Exception as e:
        response = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
        print(f"Error in elicitation-result hook: {e}", file=sys.stderr)
        sys.exit(0)  # Never block on errors


if __name__ == "__main__":
    main()
