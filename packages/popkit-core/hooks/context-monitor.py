#!/usr/bin/env python3
"""
Context Token Monitor Hook
Tracks cumulative input tokens and warns before context window exhaustion.

Compaction awareness (Issue #314):
- Detects when compaction has occurred by checking compaction-log.json
- Resets token tracking after compaction (compacted context is smaller)
- Adjusts suggestions to note that PreCompact hook preserves state

Part of PopKit plugin - Issue #16, #314
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def _get_plugin_data_dir() -> Path:
    """Get plugin data directory (CLAUDE_PLUGIN_DATA or fallback)."""
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return Path(plugin_data)
    return Path.cwd() / ".claude" / "popkit"


# Context window limits by model (approximate)
# Updated for CC 2.1.79: Models now support up to 1M context tokens.
# The default remains 200k for standard plans; 1M is available with
# extended-context plans (e.g., Opus 4.6 1M). Adjust per your plan.
MODEL_CONTEXT_LIMITS = {
    "claude-opus-4-6-1m": 1000000,  # Opus 4.6 with 1M context
    "claude-opus-4": 200000,
    "claude-sonnet-4": 200000,
    "claude-sonnet-4-5": 200000,
    "claude-haiku-4": 200000,
    "default": 200000,
}

# Warning thresholds
# NOTE (2026-03-19 audit): With 1M context now available, these thresholds
# fire much later in absolute terms (e.g., 80% of 1M = 800k tokens).
# The percentages remain appropriate since the *relative* concern is the same:
# running out of context still causes session loss regardless of window size.
THRESHOLDS = {
    "info": 0.60,  # 60% - informational
    "warning": 0.80,  # 80% - suggest summarization
    "critical": 0.90,  # 90% - suggest session capture
    "danger": 0.95,  # 95% - urgent warning
}


class ContextMonitor:
    def __init__(self):
        self.claude_dir = Path.home() / ".claude"
        self.project_claude_dir = Path.cwd() / ".claude"
        self.session_file = self.get_session_file()
        self.session_data = self.load_session_data()

    def get_session_file(self) -> Path:
        """Get path for session token tracking file.

        Prefers project-local .claude/ if it exists, otherwise uses global.
        """
        if self.project_claude_dir.exists():
            return self.project_claude_dir / "session-tokens.json"
        return self.claude_dir / "session-tokens.json"

    def load_session_data(self) -> Dict[str, Any]:
        """Load existing session token data."""
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass  # Corrupt or unreadable session file; return fresh defaults

        return {
            "session_start": datetime.now().isoformat(),
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "tool_calls": 0,
            "last_updated": datetime.now().isoformat(),
            "warnings_shown": [],
            "compactions_detected": 0,
            "last_compaction_at": None,
        }

    def save_session_data(self):
        """Save session token data."""
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            self.session_data["last_updated"] = datetime.now().isoformat()
            with open(self.session_file, "w") as f:
                json.dump(self.session_data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save token data: {e}", file=sys.stderr)

    def get_model_limit(self, model: str = None) -> int:
        """Get context limit for the current model."""
        if model:
            for key, limit in MODEL_CONTEXT_LIMITS.items():
                if key in model.lower():
                    return limit
        return MODEL_CONTEXT_LIMITS["default"]

    def update_tokens(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update token counts from input data."""
        # Extract token info from input
        # Note: Actual token counts come from API response metadata
        input_tokens = input_data.get("input_tokens", 0)
        output_tokens = input_data.get("output_tokens", 0)

        # Also check nested locations
        if not input_tokens:
            usage = input_data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

        # Update cumulative counts
        if input_tokens:
            self.session_data["total_input_tokens"] += input_tokens
        if output_tokens:
            self.session_data["total_output_tokens"] += output_tokens

        self.session_data["tool_calls"] += 1

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_input": self.session_data["total_input_tokens"],
            "total_output": self.session_data["total_output_tokens"],
            "tool_calls": self.session_data["tool_calls"],
        }

    def check_thresholds(self, model: str = None) -> Dict[str, Any]:
        """Check if any warning thresholds are exceeded."""
        limit = self.get_model_limit(model)
        total = self.session_data["total_input_tokens"]
        usage_ratio = total / limit if limit > 0 else 0

        result = {
            "usage_ratio": usage_ratio,
            "usage_percent": round(usage_ratio * 100, 1),
            "total_tokens": total,
            "limit": limit,
            "level": "ok",
            "warning": None,
            "suggestion": None,
        }

        # Include compaction count in context for suggestions
        compactions = self.session_data.get("compactions_detected", 0)
        compaction_note = (
            f" (after {compactions} compaction{'s' if compactions != 1 else ''})"
            if compactions > 0
            else ""
        )

        if usage_ratio >= THRESHOLDS["danger"]:
            result["level"] = "danger"
            result["warning"] = (
                f"URGENT: Context at {result['usage_percent']}% capacity"
                f" ({total:,}/{limit:,} tokens){compaction_note}"
            )
            result["suggestion"] = (
                "Run /popkit:session-capture IMMEDIATELY."
                " PreCompact hook will auto-save state if compaction triggers,"
                " but manual capture preserves more detail."
            )
        elif usage_ratio >= THRESHOLDS["critical"]:
            result["level"] = "critical"
            result["warning"] = (
                f"Context at {result['usage_percent']}% capacity"
                f" ({total:,}/{limit:,} tokens){compaction_note}"
            )
            result["suggestion"] = (
                "Strongly recommend: /popkit:session-capture to save state now."
                " PreCompact hook will auto-snapshot if compaction occurs."
            )
        elif usage_ratio >= THRESHOLDS["warning"]:
            result["level"] = "warning"
            result["warning"] = (
                f"Context at {result['usage_percent']}% capacity"
                f" ({total:,}/{limit:,} tokens){compaction_note}"
            )
            result["suggestion"] = (
                "Consider: /popkit:session-capture to save state, or summarize conversation."
                " Compaction will auto-preserve git state via PreCompact hook."
            )
        elif usage_ratio >= THRESHOLDS["info"]:
            result["level"] = "info"
            # Info level doesn't show warning, just tracks

        return result

    def should_show_warning(self, level: str) -> bool:
        """Check if we should show this warning (avoid spam)."""
        warnings_shown = self.session_data.get("warnings_shown", [])

        # Always show danger/critical
        if level in ["danger", "critical"]:
            return True

        # Only show warning level once per session
        if level == "warning" and "warning" not in warnings_shown:
            self.session_data["warnings_shown"].append("warning")
            return True

        return False

    def check_for_recent_compaction(self) -> bool:
        """Detect if compaction has occurred since our last check.

        Reads the compaction log written by pre-compact.py and compares
        the count to what we last saw. If compaction happened, reset
        token tracking (compacted context is smaller than the sum of
        all previous tokens) and note it in session data.

        Returns True if a new compaction was detected.
        """
        log_file = _get_plugin_data_dir() / "compaction-log.json"
        if not log_file.exists():
            return False

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                events = json.load(f)

            current_count = len(events)
            tracked_count = self.session_data.get("compactions_detected", 0)

            if current_count > tracked_count:
                # New compaction detected -- reset token counters
                # After compaction, the actual context is much smaller than
                # the cumulative total we were tracking, so our numbers are stale.
                self.session_data["compactions_detected"] = current_count
                self.session_data["last_compaction_at"] = datetime.now().isoformat()

                # Reset cumulative tokens (they no longer reflect reality)
                self.session_data["total_input_tokens"] = 0
                self.session_data["total_output_tokens"] = 0
                self.session_data["tool_calls"] = 0

                # Clear warning state so thresholds can fire again fresh
                self.session_data["warnings_shown"] = []

                return True

        except (json.JSONDecodeError, OSError):
            pass  # Compaction file unreadable; assume no new compaction

        return False

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing function."""
        result = {
            "status": "success",
            "tokens": {},
            "threshold_check": {},
            "display": None,
        }

        # Check for recent compaction before updating tokens
        compaction_detected = self.check_for_recent_compaction()
        if compaction_detected:
            result["compaction_detected"] = True
            result["compaction_count"] = self.session_data.get(
                "compactions_detected", 0
            )

        # Update token counts
        tokens = self.update_tokens(input_data)
        result["tokens"] = tokens

        # Check thresholds
        model = input_data.get("model")
        threshold_check = self.check_thresholds(model)
        result["threshold_check"] = threshold_check

        # Generate display if warning needed
        if threshold_check["level"] != "ok" and self.should_show_warning(
            threshold_check["level"]
        ):
            result["display"] = {
                "level": threshold_check["level"],
                "warning": threshold_check["warning"],
                "suggestion": threshold_check["suggestion"],
            }

        # Save updated data
        self.save_session_data()

        return result


def main():
    """Main entry point - JSON stdin/stdout protocol."""
    try:
        input_data = json.loads(sys.stdin.read())

        monitor = ContextMonitor()
        result = monitor.process(input_data)

        # Output warnings to stderr for visibility
        display = result.get("display")
        if display:
            level = display["level"]
            if level == "danger":
                print(f"\n{'=' * 60}", file=sys.stderr)
                print(f"🔴 {display['warning']}", file=sys.stderr)
                print(f"💡 {display['suggestion']}", file=sys.stderr)
                print(f"{'=' * 60}\n", file=sys.stderr)
            elif level == "critical":
                print(f"\n🔴 {display['warning']}", file=sys.stderr)
                print(f"💡 {display['suggestion']}", file=sys.stderr)
            elif level == "warning":
                print(f"\n⚠️  {display['warning']}", file=sys.stderr)
                print(f"💡 {display['suggestion']}", file=sys.stderr)

        # Output JSON response
        print(json.dumps(result))

    except json.JSONDecodeError as e:
        response = {"status": "error", "error": f"Invalid JSON: {e}"}
        print(json.dumps(response))
        sys.exit(1)
    except Exception as e:
        response = {"status": "error", "error": str(e)}
        print(json.dumps(response))
        sys.exit(0)  # Don't block on errors


if __name__ == "__main__":
    main()
