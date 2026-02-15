#!/usr/bin/env python3
"""
Global Pre-Tool-Use Hook
Safety checks, agent coordination, and orchestration before tool execution
Prevents dangerous operations and coordinates multi-agent workflows
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional import for observability features (not required for core functionality)
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Import error code system (Issue #104)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared-py"))
    from popkit_shared.utils.error_codes import ErrorRegistry, ErrorResponse

    HAS_ERROR_CODES = True
except ImportError:
    HAS_ERROR_CODES = False

# No longer using premium/tier-based gating (Epic #580, Issue #581)
# All features work without API key - API key only adds enhancements
# Premium checking code removed - see enhancement_detector.py for optional enhancements
PREMIUM_CHECKER_AVAILABLE = False

# Import skill state tracker for AskUserQuestion enforcement (Issue #159)
try:
    from skill_state import get_tracker

    SKILL_STATE_AVAILABLE = True
except ImportError:
    SKILL_STATE_AVAILABLE = False

# Import tool filter for context optimization (Issue #275)
try:
    from tool_filter import ToolFilter

    TOOL_FILTER_AVAILABLE = True
except ImportError:
    TOOL_FILTER_AVAILABLE = False

# Import session recorder for forensic analysis (Issue #603)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared-py"))
    from popkit_shared.utils.session_recorder import get_recorder, is_recording_enabled

    SESSION_RECORDER_AVAILABLE = True
except ImportError:
    SESSION_RECORDER_AVAILABLE = False

# Import XML parser for robust ElementTree-based parsing (XML Testing Strategy)
try:
    from popkit_shared.utils.xml_parser import (
        parse_problem_context,
        parse_project_context,
    )

    XML_PARSER_AVAILABLE = True
except ImportError:
    XML_PARSER_AVAILABLE = False


class PreToolUseHook:
    def __init__(self):
        self.claude_dir = Path.home() / ".claude"
        self.config_dir = self.claude_dir / "config"
        self.session_id = self.get_session_id()
        self.observability_endpoint = "http://localhost:8001/events"
        self.orchestrator_endpoint = "http://localhost:8005/coordinate"

        # Load configuration
        self.safety_rules = self.load_safety_rules()
        self.coordination_rules = self.load_coordination_rules()
        self.tool_permissions = self.load_tool_permissions()

        # Initialize context database
        self.context_db = self.init_context_db()

    def get_session_id(self) -> str:
        """Get current session ID from environment or generate new one"""
        session_id = os.environ.get("CLAUDE_SESSION_ID")
        if not session_id:
            # Try to get from recent context
            try:
                db_path = self.config_dir / "context-memory.db"
                if db_path.exists():
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.execute(
                        "SELECT session_id FROM context_memory ORDER BY created_at DESC LIMIT 1"
                    )
                    result = cursor.fetchone()
                    if result:
                        session_id = result[0]
                    conn.close()
            except Exception:
                # Best-effort fallback: ignore optional failure.
                pass

        return session_id or "unknown"

    def load_safety_rules(self) -> Dict[str, Any]:
        """Load safety rules for dangerous operations (Issue #213 - platform-aware paths)"""
        return {
            "blocked_commands": [
                r"rm\s+-rf\s+/",
                r"sudo\s+rm\s+-rf",
                r"format\s+c:",
                r"del\s+/s\s+/q\s+c:",
                r"DROP\s+DATABASE",
                r"TRUNCATE\s+TABLE",
                r"chmod\s+777",
                r"chown\s+root",
                r"dd\s+if=/dev/zero",
                r":(){ :|:& };:",  # Fork bomb
            ],
            "sensitive_paths": {
                # Unix/Linux paths (apply to Linux, macOS, WSL, Git Bash)
                "unix": [
                    r"\/etc\/passwd",
                    r"\/etc\/shadow",
                    r"\/root\/",
                    r"\/boot\/",
                    r"\.ssh\/id_rsa",
                    r"\.ssh\/id_ed25519",
                    r"\.aws\/credentials",
                    r"\.env",
                ],
                # Windows-specific paths
                "windows": [
                    r"C:\\Windows\\",
                    r"C:\\Windows\\System32",
                    r"C:\\Program Files\\",
                    r"C:\\Program Files \(x86\)\\",
                    r"%APPDATA%",
                    r"%LOCALAPPDATA%",
                    r"%PROGRAMDATA%",
                    r"C:\\ProgramData\\",
                    r"HKEY_",  # Registry paths
                    r"HKLM\\",
                    r"HKCU\\",
                ],
                # macOS-specific paths
                "darwin": [
                    r"\/System\/",
                    r"\/Library\/System\/",
                    r"~\/Library\/Preferences\/",
                    r"\/private\/var\/",
                    r"\/usr\/bin\/",
                    r"\/usr\/sbin\/",
                    r"\/Applications\/",
                ],
                # Cross-platform temp/cache directories
                "all": [
                    r"\/tmp\/",
                    r"\/var\/tmp\/",
                    r"C:\\Windows\\Temp\\",
                    r"%TEMP%",
                    r"~\/\.cache\/",
                ],
            },
            "dangerous_tools": [
                "Bash:rm -rf",
                "Bash:sudo",
                "Bash:chmod 777",
                "Write:/etc/",
                "Write:/root/",
                "Edit:/etc/",
            ],
        }

    def load_coordination_rules(self) -> Dict[str, Any]:
        """Load agent coordination and conflict resolution rules"""
        return {
            "tool_conflicts": {
                "Edit": ["Write", "MultiEdit"],
                "Write": ["Edit", "MultiEdit"],
                "MultiEdit": ["Edit", "Write"],
            },
            "agent_priorities": {
                "security": ["security-auditor", "security-tester"],
                "performance": [
                    "performance-optimizer",
                    "load-tester",
                    "performance-profiler",
                ],
                "quality": ["code-reviewer", "quality-assurance-coordinator"],
                "testing": [
                    "automated-tester",
                    "manual-tester",
                    "compatibility-tester",
                ],
            },
            "sequential_operations": [
                ["security-auditor", "code-reviewer"],
                ["test-writer-fixer", "automated-tester"],
                ["ui-designer", "accessibility-guardian"],
            ],
            "parallel_operations": [
                ["performance-optimizer", "seo-optimizer"],
                ["growth-hacker", "tiktok-strategist"],
                ["feedback-synthesizer", "trend-researcher"],
            ],
        }

    def load_tool_permissions(self) -> Dict[str, Dict[str, Any]]:
        """Load tool permission matrix by context"""
        return {
            "production": {
                "allowed_tools": ["Read", "Grep", "Glob", "LS", "WebFetch"],
                "restricted_tools": ["Write", "Edit", "MultiEdit", "Bash"],
                "requires_confirmation": ["Write", "Edit", "MultiEdit"],
            },
            "development": {
                "allowed_tools": [
                    "Read",
                    "Write",
                    "Edit",
                    "MultiEdit",
                    "Grep",
                    "Glob",
                    "LS",
                    "Bash",
                    "WebFetch",
                ],
                "restricted_tools": [],
                "requires_confirmation": ["Bash:rm", "Bash:sudo", "Write:/"],
            },
            "testing": {
                "allowed_tools": [
                    "Read",
                    "Write",
                    "Edit",
                    "MultiEdit",
                    "Grep",
                    "Glob",
                    "LS",
                    "Bash",
                    "WebFetch",
                ],
                "restricted_tools": ["Bash:rm -rf", "Write:/etc/"],
                "requires_confirmation": ["Bash", "Write"],
            },
        }

    def init_context_db(self) -> Optional[sqlite3.Connection]:
        """Initialize context database connection"""
        try:
            db_path = self.config_dir / "context-memory.db"
            if db_path.exists():
                return sqlite3.connect(str(db_path))
        except Exception:
            # Best-effort fallback: ignore optional failure.
            pass
        return None

    def detect_environment_context(self) -> str:
        """Detect current environment context (production, development, testing)"""
        cwd = os.getcwd()

        # Check for production indicators
        if any(indicator in cwd.lower() for indicator in ["prod", "production", "live", "deploy"]):
            return "production"

        # Check for testing indicators
        if any(indicator in cwd.lower() for indicator in ["test", "testing", "spec", "qa"]):
            return "testing"

        # Check for development indicators or default
        return "development"

    def get_platform_sensitive_paths(self) -> List[str]:
        """Get platform-specific sensitive paths for security checks (Issue #213)"""
        sensitive_paths_dict = self.safety_rules.get("sensitive_paths", {})

        # If it's still a list (old format), return as-is for backward compatibility
        if isinstance(sensitive_paths_dict, list):
            return sensitive_paths_dict

        # Determine platform
        platform = sys.platform.lower()

        # Collect applicable paths
        paths = []

        # Always include cross-platform paths
        paths.extend(sensitive_paths_dict.get("all", []))

        # Add platform-specific paths
        if platform == "win32" or platform == "cygwin":
            # Windows paths
            paths.extend(sensitive_paths_dict.get("windows", []))

            # Check if running in Git Bash or WSL (Unix commands on Windows)
            if "MSYSTEM" in os.environ or "WSL_DISTRO_NAME" in os.environ:
                paths.extend(sensitive_paths_dict.get("unix", []))
        elif platform == "darwin":
            # macOS paths (includes unix paths)
            paths.extend(sensitive_paths_dict.get("unix", []))
            paths.extend(sensitive_paths_dict.get("darwin", []))
        elif platform.startswith("linux"):
            # Linux paths
            paths.extend(sensitive_paths_dict.get("unix", []))
        else:
            # Unknown platform - use unix as fallback
            paths.extend(sensitive_paths_dict.get("unix", []))

        return paths

    def check_safety_violations(self, tool_name: str, tool_args: Dict[str, Any]) -> List[str]:
        """Check for safety violations in tool usage (Issue #213 - platform-aware paths)"""
        violations = []

        # Check blocked commands for Bash tool
        if tool_name == "Bash" and "command" in tool_args:
            command = tool_args["command"]
            for blocked_pattern in self.safety_rules["blocked_commands"]:
                if re.search(blocked_pattern, command, re.IGNORECASE):
                    violations.append(f"Blocked dangerous command: {blocked_pattern}")

        # Check sensitive paths for file operations (platform-aware)
        if tool_name in ["Write", "Edit", "MultiEdit"] and "file_path" in tool_args:
            file_path = tool_args["file_path"]

            # Get platform-specific sensitive paths
            sensitive_paths = self.get_platform_sensitive_paths()

            for sensitive_pattern in sensitive_paths:
                if re.search(sensitive_pattern, file_path, re.IGNORECASE):
                    violations.append(f"Access to sensitive path blocked: {sensitive_pattern}")

        # Check dangerous tool combinations
        tool_signature = f"{tool_name}:{tool_args.get('command', tool_args.get('file_path', ''))}"
        for dangerous_tool in self.safety_rules["dangerous_tools"]:
            if dangerous_tool in tool_signature:
                violations.append(f"Dangerous tool usage blocked: {dangerous_tool}")

        return violations

    def check_permission_requirements(
        self, tool_name: str, tool_args: Dict[str, Any], context: str
    ) -> Tuple[bool, List[str]]:
        """Check if tool usage requires special permissions or confirmation"""
        permissions = self.tool_permissions.get(context, self.tool_permissions["development"])
        warnings = []

        # Check if tool is allowed
        if (
            tool_name not in permissions["allowed_tools"]
            and tool_name in permissions["restricted_tools"]
        ):
            return False, [f"Tool {tool_name} is restricted in {context} environment"]

        # Check if confirmation is required
        tool_signature = f"{tool_name}:{tool_args.get('command', tool_args.get('file_path', ''))}"
        for confirmation_pattern in permissions["requires_confirmation"]:
            if confirmation_pattern in tool_signature:
                warnings.append(f"Tool {tool_name} requires confirmation in {context} environment")

        return True, warnings

    def coordinate_with_agents(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate tool usage with active agents"""
        coordination_result = {
            "conflicts": [],
            "recommendations": [],
            "agent_handoffs": [],
            "sequential_requirements": [],
        }

        # Check for tool conflicts
        if tool_name in self.coordination_rules["tool_conflicts"]:
            conflicting_tools = self.coordination_rules["tool_conflicts"][tool_name]
            coordination_result["conflicts"] = [
                f"Tool {tool_name} conflicts with: {', '.join(conflicting_tools)}"
            ]

        # Get agent recommendations based on tool usage
        if tool_name == "Write" and "file_path" in tool_args:
            file_path = tool_args["file_path"]
            if file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
                coordination_result["recommendations"].append(
                    "Consider running code-reviewer after file modifications"
                )
            if file_path.endswith((".test.ts", ".spec.ts")):
                coordination_result["recommendations"].append(
                    "Consider running automated-tester after test file changes"
                )

        # Check for required sequential operations
        for sequence in self.coordination_rules["sequential_operations"]:
            if len(sequence) > 1:
                coordination_result["sequential_requirements"].append(
                    f"After completion, consider: {' → '.join(sequence[1:])}"
                )

        return coordination_result

    def log_pre_tool_event(
        self, tool_name: str, tool_args: Dict[str, Any], safety_check: Dict[str, Any]
    ):
        """Log pre-tool-use event to observability system"""
        if not HAS_REQUESTS:
            return
        try:
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "sessionId": self.session_id,
                "eventType": "pre_tool_use",
                "hookType": "pre_tool_use",
                "toolName": tool_name,
                "toolArgs": tool_args,
                "metadata": {
                    "safety_check": safety_check,
                    "environment_context": self.detect_environment_context(),
                    "working_directory": os.getcwd(),
                },
            }

            response = requests.post(self.observability_endpoint, json=event_data, timeout=2)

            if response.status_code != 200:
                print(
                    f"Warning: Observability logging failed: {response.status_code}",
                    file=sys.stderr,
                )

        except Exception as e:
            print(f"Warning: Could not log to observability system: {e}", file=sys.stderr)

    def request_orchestration(
        self, tool_name: str, tool_args: Dict[str, Any], coordination: Dict[str, Any]
    ) -> Optional[Dict]:
        """Request orchestration guidance from orchestrator service"""
        if not HAS_REQUESTS:
            return None
        try:
            orchestration_data = {
                "session_id": self.session_id,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "coordination_analysis": coordination,
                "environment_context": self.detect_environment_context(),
                "timestamp": datetime.now().isoformat(),
            }

            response = requests.post(self.orchestrator_endpoint, json=orchestration_data, timeout=3)

            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f"Warning: Orchestration request failed: {response.status_code}",
                    file=sys.stderr,
                )

        except Exception as e:
            print(f"Warning: Could not connect to orchestrator: {e}", file=sys.stderr)

        return None

    def get_recent_context(self) -> Dict[str, Any]:
        """Get recent context from previous interactions"""
        context = {"recent_tools": [], "recent_agents": [], "project_context": {}}

        if not self.context_db:
            return context

        try:
            # Get recent tool usage
            cursor = self.context_db.execute(
                """
                SELECT tool_name, COUNT(*) as usage_count
                FROM pre_tool_events
                WHERE session_id = ? AND timestamp > datetime('now', '-1 hour')
                GROUP BY tool_name
                ORDER BY usage_count DESC
                LIMIT 5
            """,
                (self.session_id,),
            )

            context["recent_tools"] = [
                {"tool": row[0], "count": row[1]} for row in cursor.fetchall()
            ]

        except Exception as e:
            print(f"Warning: Could not retrieve recent context: {e}", file=sys.stderr)

        return context

    def parse_xml_context(
        self, conversation_history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse XML context from recent messages for agent routing (Phase 1: XML Integration #516).

        Searches conversation history for XML context generated by user-prompt-submit hook.
        Extracts category, severity, and workflow from <problem-context> tag.
        Uses robust ElementTree parsing with regex fallback.

        Args:
            conversation_history: List of recent messages with role and content

        Returns:
            Dict with parsed context or None if no XML found:
            {
                "category": str,  # bug, feature, optimization, etc.
                "severity": str,  # critical, high, medium, low
                "workflow": Dict,  # workflow structure with steps
                "stack": List[str],  # detected tech stack
                "infrastructure": Dict[str, Any]  # detected infrastructure
            }

        Example:
            >>> history = [{"role": "user", "content": "...<problem-context><category>bug</category>..."}]
            >>> parse_xml_context(history)
            {'category': 'bug', 'severity': 'high', 'workflow': {...}}
        """
        try:
            # Search recent messages for XML context (check last 5 messages)
            for message in reversed(conversation_history[-5:]):
                content = message.get("content", "")

                # Look for XML context markers
                if "<!-- XML Context (Invisible) -->" not in content:
                    continue

                # Extract XML content between markers
                xml_start = content.find("<!-- XML Context (Invisible) -->")
                xml_end = content.find("<!-- End XML Context -->")

                if xml_start == -1 or xml_end == -1:
                    continue

                xml_content = content[
                    xml_start + len("<!-- XML Context (Invisible) -->") : xml_end
                ].strip()

                # Try ElementTree parsing first (robust)
                if XML_PARSER_AVAILABLE:
                    try:
                        # Look for problem-context element
                        problem_match = re.search(
                            r"<problem-context[^>]*>.*?</problem-context>",
                            xml_content,
                            re.DOTALL,
                        )
                        if problem_match:
                            problem_xml_str = problem_match.group(0)
                            problem_data = parse_problem_context(problem_xml_str)

                            if problem_data and problem_data.get("category"):
                                parsed_context = {
                                    "category": problem_data.get("category"),
                                    "severity": problem_data.get("severity"),
                                    "workflow": problem_data.get("workflow"),
                                }

                                # Parse project context for stack and infrastructure
                                project_match = re.search(
                                    r"<project[^>]*>.*?</project>",
                                    xml_content,
                                    re.DOTALL,
                                )
                                if project_match:
                                    project_xml_str = project_match.group(0)
                                    project_data = parse_project_context(project_xml_str)

                                    if project_data:
                                        if project_data.get("stack"):
                                            parsed_context["stack"] = project_data["stack"]
                                        if project_data.get("infrastructure"):
                                            parsed_context["infrastructure"] = project_data[
                                                "infrastructure"
                                            ]

                                return parsed_context

                    except Exception as e:
                        print(
                            f"ElementTree parsing failed, falling back to regex: {e}",
                            file=sys.stderr,
                        )
                        # Fall through to regex fallback

                # Fallback to regex parsing (backward compatibility)
                parsed_context = {}

                # Parse problem context (support both <problem> and <problem-context>)
                problem_match = re.search(
                    r"<problem-context[^>]*>(.*?)</problem-context>",
                    xml_content,
                    re.DOTALL,
                )
                if not problem_match:
                    problem_match = re.search(r"<problem>(.*?)</problem>", xml_content, re.DOTALL)

                if problem_match:
                    problem_xml = problem_match.group(1)

                    # Category (required)
                    category_match = re.search(r"<category>(.*?)</category>", problem_xml)
                    if category_match:
                        parsed_context["category"] = category_match.group(1).strip()

                    # Severity (optional)
                    severity_match = re.search(r"<severity>(.*?)</severity>", problem_xml)
                    if severity_match:
                        parsed_context["severity"] = severity_match.group(1).strip()

                    # Workflow (optional) - store as string for backward compatibility
                    workflow_match = re.search(
                        r"<workflow>(.*?)</workflow>", problem_xml, re.DOTALL
                    )
                    if workflow_match:
                        parsed_context["workflow"] = workflow_match.group(1).strip()

                # Parse project context for stack and infrastructure
                project_match = re.search(r"<project[^>]*>(.*?)</project>", xml_content, re.DOTALL)
                if not project_match:
                    project_match = re.search(
                        r"<project-context>(.*?)</project-context>",
                        xml_content,
                        re.DOTALL,
                    )

                if project_match:
                    project_xml = project_match.group(1)

                    # Extract stack (support both <technology> and <item>)
                    stack_items = re.findall(r"<technology>(.*?)</technology>", project_xml)
                    if not stack_items:
                        stack_items = re.findall(r"<item>(.*?)</item>", project_xml)
                    if stack_items:
                        parsed_context["stack"] = stack_items

                    # Extract infrastructure
                    infra_match = re.search(
                        r"<infrastructure>(.*?)</infrastructure>",
                        project_xml,
                        re.DOTALL,
                    )
                    if infra_match:
                        infra_xml = infra_match.group(1)
                        infrastructure = {}

                        # Parse each infrastructure item (e.g., <redis>true</redis>)
                        for service in [
                            "redis",
                            "postgres",
                            "mongodb",
                            "mysql",
                            "elasticsearch",
                            "rabbitmq",
                            "kafka",
                            "docker",
                            "kubernetes",
                            "cloudflare",
                            "aws",
                            "gcp",
                            "azure",
                        ]:
                            service_match = re.search(f"<{service}>(.*?)</{service}>", infra_xml)
                            if service_match:
                                infrastructure[service] = (
                                    service_match.group(1).strip().lower() == "true"
                                )

                        parsed_context["infrastructure"] = infrastructure

                # Return parsed context if we found at least a category
                if "category" in parsed_context:
                    return parsed_context

            # No XML context found
            return None

        except Exception as e:
            print(f"Warning: XML context parsing failed: {e}", file=sys.stderr)
            return None

    def suggest_agent_from_context(self, xml_context: Dict[str, Any]) -> Optional[str]:
        """
        Suggest appropriate agent based on XML context category and severity (Phase 1: XML Integration #516).

        Maps problem categories to specialized agents:
        - bug → bug-whisperer (for complex debugging)
        - feature → refactoring-expert (for code structure)
        - optimization → performance-optimizer (for performance)
        - refactor → refactoring-expert
        - security → security-auditor
        - test → test-writer-fixer
        - docs → documentation-maintainer

        Considers severity for agent selection:
        - critical/high bugs → bug-whisperer
        - medium/low bugs → code-reviewer

        Args:
            xml_context: Parsed XML context with category, severity, stack, infrastructure

        Returns:
            Agent name or None if no specific agent recommended

        Example:
            >>> suggest_agent_from_context({"category": "bug", "severity": "critical"})
            'bug-whisperer'
            >>> suggest_agent_from_context({"category": "feature"})
            'refactoring-expert'
        """
        if not xml_context or "category" not in xml_context:
            return None

        category = xml_context.get("category", "").lower()
        severity = xml_context.get("severity", "medium").lower()

        # Category-to-agent mapping
        agent_map = {
            "bug": "bug-whisperer" if severity in ["critical", "high"] else "code-reviewer",
            "feature": "refactoring-expert",
            "optimization": "performance-optimizer",
            "refactor": "refactoring-expert",
            "security": "security-auditor",
            "test": "test-writer-fixer",
            "docs": "documentation-maintainer",
            "documentation": "documentation-maintainer",
            "investigation": "code-reviewer",
            "task": None,  # Generic tasks don't need specific agent
        }

        suggested_agent = agent_map.get(category)

        # Additional logic based on infrastructure context
        infrastructure = xml_context.get("infrastructure", {})

        # If database-heavy task, consider query-optimizer
        if category == "optimization" and any(
            db in infrastructure for db in ["postgres", "mysql", "mongodb"]
        ):
            suggested_agent = "query-optimizer"

        # If security-related infrastructure detected, escalate to security-auditor
        if any(sec in infrastructure for sec in ["redis", "elasticsearch"]) and category in [
            "bug",
            "feature",
        ]:
            # Don't override, but note in metadata
            pass

        return suggested_agent

    def store_pre_tool_context(
        self, tool_name: str, tool_args: Dict[str, Any], safety_result: Dict[str, Any]
    ):
        """Store pre-tool context for future reference"""
        if not self.context_db:
            return

        try:
            # Create table if it doesn't exist
            self.context_db.execute("""
                CREATE TABLE IF NOT EXISTS pre_tool_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    tool_args TEXT,
                    safety_result TEXT,
                    environment_context TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert current event
            self.context_db.execute(
                """
                INSERT INTO pre_tool_events 
                (session_id, timestamp, tool_name, tool_args, safety_result, environment_context)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    self.session_id,
                    datetime.now().isoformat(),
                    tool_name,
                    json.dumps(tool_args),
                    json.dumps(safety_result),
                    self.detect_environment_context(),
                ),
            )

            self.context_db.commit()

        except Exception as e:
            print(f"Warning: Could not store pre-tool context: {e}", file=sys.stderr)

    # Premium gating removed (Epic #580, Issue #581)
    # All features work without API key - no feature gating or rate limiting
    # API key only adds semantic intelligence enhancements

    def track_skill_invocation(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Track skill invocations for AskUserQuestion enforcement (Issue #159).

        Follows Anthropic's recommendation from the Hooks Guide:
        "By encoding these rules as hooks rather than prompting instructions,
        you turn suggestions into app-level code that executes every time."

        Args:
            tool_name: Name of tool being invoked
            tool_args: Tool arguments

        Returns:
            Dict with tracking info and any required decision prompts
        """
        if not SKILL_STATE_AVAILABLE:
            return {"tracked": False}

        tracker = get_tracker()

        # If this is a Skill invocation, start tracking it
        if tool_name == "Skill":
            skill_name = tool_args.get("skill", "")
            tracker.start_skill(skill_name)
            return {"tracked": True, "skill_started": skill_name}

        # If this is AskUserQuestion, record the decision
        if tool_name == "AskUserQuestion":
            questions = tool_args.get("questions", [])
            if questions:
                header = questions[0].get("header", "")
                tracker.record_decision_by_header(header)
            return {"tracked": True, "decision_recorded": True}

        # Record this tool use for tracking
        tracker.record_tool_use(tool_name)
        return {"tracked": True}

    def determine_workflow(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Determine workflow from tool context for tool filtering (Issue #275).

        Args:
            tool_name: Name of tool being invoked
            tool_args: Tool arguments

        Returns:
            Workflow name or 'unknown'
        """
        # Map tools to workflows
        workflow_map = {
            "Edit": "file-edit",
            "Write": "file-edit",
        }

        # Check if this is a git operation
        if tool_name == "Bash":
            command = tool_args.get("command", "")
            if "git" in command:
                if "commit" in command or "add" in command:
                    return "git-commit"
            # Other bash operations get full access
            return "full-access"

        return workflow_map.get(tool_name, "unknown")

    def filter_tools_for_context(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply tool filtering for context optimization (Issue #275).

        This is currently in passthrough mode - it logs what would be filtered
        but doesn't actually block anything. Future: enable active filtering.

        Args:
            tool_name: Name of tool being invoked
            tool_args: Tool arguments

        Returns:
            Dict with filtering info
        """
        if not TOOL_FILTER_AVAILABLE:
            return {"filtered": False}

        # Determine workflow
        workflow = self.determine_workflow(tool_name, tool_args)

        # Get available tools (default set)
        available_tools = [
            "Read",
            "Write",
            "Edit",
            "Bash",
            "Grep",
            "Glob",
            "Task",
            "TodoWrite",
            "WebFetch",
            "WebSearch",
            "AskUserQuestion",
        ]

        # Apply filtering
        tool_filter = ToolFilter()
        filtered_tools = tool_filter.filter(workflow, available_tools)

        # Calculate reduction
        reduction = len(available_tools) - len(filtered_tools)

        return {
            "filtered": True,
            "workflow": workflow,
            "original_count": len(available_tools),
            "filtered_count": len(filtered_tools),
            "reduction": reduction,
            "filtered_tools": filtered_tools,
        }

    def process_tool_request(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Main processing function for tool requests"""
        result = {
            "action": "continue",
            "tool_name": tool_name,
            "tool_args": tool_args,
            "session_id": self.session_id,
            "safety_check": {"passed": True, "violations": []},
            "coordination": {},
            "warnings": [],
            "recommendations": [],
            "premium_check": {},
            "xml_context": None,
            "suggested_agent": None,
        }

        # Environment context detection
        environment_context = self.detect_environment_context()

        # Parse XML context from conversation history for agent routing (Phase 1: XML Integration #516)
        if conversation_history:
            xml_context = self.parse_xml_context(conversation_history)
            result["xml_context"] = xml_context

            # Suggest agent based on XML context
            if xml_context:
                suggested_agent = self.suggest_agent_from_context(xml_context)
                result["suggested_agent"] = suggested_agent

                # Log XML-based routing to stderr
                if suggested_agent:
                    print(
                        f"🤖 XML-Based Routing: {xml_context.get('category', 'unknown')} → {suggested_agent}",
                        file=sys.stderr,
                    )
                    if xml_context.get("severity"):
                        print(
                            f"   Severity: {xml_context.get('severity')}",
                            file=sys.stderr,
                        )

        # Skill state tracking for AskUserQuestion enforcement (Issue #159)
        skill_tracking = self.track_skill_invocation(tool_name, tool_args)
        result["skill_tracking"] = skill_tracking

        # Tool filtering for context optimization (Issue #275)
        tool_filtering = self.filter_tools_for_context(tool_name, tool_args)
        result["tool_filtering"] = tool_filtering
        if tool_filtering.get("filtered"):
            # Log filtering info to stderr (passthrough mode - not blocking)
            print(
                f"🔧 Tool Filtering (Passthrough): {tool_filtering['workflow']}",
                file=sys.stderr,
            )
            print(
                f"   Tools: {tool_filtering['original_count']} → {tool_filtering['filtered_count']} ({tool_filtering['reduction']} filtered)",
                file=sys.stderr,
            )

        # Safety checks
        safety_violations = self.check_safety_violations(tool_name, tool_args)
        if safety_violations:
            result["action"] = "block"
            result["safety_check"] = {"passed": False, "violations": safety_violations}
            return result

        # No premium gating or rate limiting (Epic #580, Issue #581)
        # All features work without API key

        # Permission checks
        permission_allowed, permission_warnings = self.check_permission_requirements(
            tool_name, tool_args, environment_context
        )
        if not permission_allowed:
            result["action"] = "block"
            result["safety_check"] = {
                "passed": False,
                "violations": permission_warnings,
            }
            return result

        result["warnings"].extend(permission_warnings)

        # Agent coordination
        coordination = self.coordinate_with_agents(tool_name, tool_args)
        result["coordination"] = coordination
        result["recommendations"].extend(coordination.get("recommendations", []))

        # Orchestration request
        orchestration_result = self.request_orchestration(tool_name, tool_args, coordination)
        if orchestration_result:
            result["orchestration"] = orchestration_result
            if orchestration_result.get("action") == "modify":
                result["tool_args"] = orchestration_result.get("modified_args", tool_args)

        # Get recent context
        result["recent_context"] = self.get_recent_context()

        # Log event
        self.log_pre_tool_event(tool_name, tool_args, result["safety_check"])

        # Store context
        self.store_pre_tool_context(tool_name, tool_args, result)

        return result


def main():
    """Main entry point for the hook - JSON stdin/stdout protocol"""
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        tool_name = input_data.get("tool_name", "")
        tool_args = input_data.get("tool_input", {})
        conversation_history = input_data.get("conversation_history", [])

        if not tool_name:
            response = {"error": "No tool_name provided in input"}
            print(json.dumps(response))
            sys.exit(1)

        # Record tool call START (before execution)
        if SESSION_RECORDER_AVAILABLE and is_recording_enabled():
            try:
                recorder = get_recorder()

                # Store transcript path as metadata (once, for HTML report generation)
                if len(recorder.events) == 1:  # Only session_start event exists
                    transcript_path = input_data.get("transcript_path")
                    if transcript_path:
                        recorder.record_event(
                            {
                                "type": "metadata",
                                "timestamp": datetime.now().isoformat(),
                                "transcript_path": transcript_path,
                            }
                        )

                recorder.record_event(
                    {
                        "type": "tool_call_start",
                        "timestamp": datetime.now().isoformat(),
                        "tool_name": tool_name,
                        "tool_use_id": input_data.get("tool_use_id"),  # For transcript correlation
                        "parameters": tool_args,
                    }
                )

                # Record assistant messages from conversation history for context
                # This captures Claude's reasoning, analysis, and recommendations
                if conversation_history:
                    # Look at recent messages (last 5) for assistant responses
                    for msg in reversed(conversation_history[-5:]):
                        if msg.get("role") == "assistant":
                            content = msg.get("content", "")

                            # Text messages contain reasoning/analysis
                            if isinstance(content, str) and content.strip():
                                recorder.record_event(
                                    {
                                        "type": "assistant_message",
                                        "timestamp": datetime.now().isoformat(),
                                        "content": content,
                                        "before_tool": tool_name,
                                    }
                                )
                            # Content can also be a list with tool_use/text blocks
                            elif isinstance(content, list):
                                for block in content:
                                    if isinstance(block, dict):
                                        # Extract text blocks (reasoning)
                                        if block.get("type") == "text":
                                            text = block.get("text", "").strip()
                                            if text:
                                                recorder.record_event(
                                                    {
                                                        "type": "assistant_message",
                                                        "timestamp": datetime.now().isoformat(),
                                                        "content": text,
                                                        "before_tool": tool_name,
                                                    }
                                                )

            except Exception as e:
                # Don't block on recording failures
                print(f"Warning: Failed to record tool start: {e}", file=sys.stderr)

        hook = PreToolUseHook()
        result = hook.process_tool_request(tool_name, tool_args, conversation_history)

        # Build JSON response
        response = {
            "decision": "approve" if result["action"] != "block" else "block",
            "reason": None,
            "tool_name": tool_name,
            "session_id": result.get("session_id"),
            "warnings": result.get("warnings", []),
            "recommendations": result.get("recommendations", []),
            "xml_context": result.get("xml_context"),
            "suggested_agent": result.get("suggested_agent"),
        }

        # CC 2.1.9+: Build additionalContext for model reasoning injection
        context_parts = []
        if result.get("warnings"):
            context_parts.append("Safety warnings: " + "; ".join(result["warnings"]))
        if result.get("suggested_agent"):
            context_parts.append(f"Suggested agent: {result['suggested_agent']}")
        if result.get("recommendations"):
            context_parts.append("Recommendations: " + "; ".join(result["recommendations"]))
        if context_parts:
            response["additionalContext"] = " | ".join(context_parts)

        if result["action"] == "block":
            violations = result["safety_check"]["violations"]
            response["reason"] = "; ".join(violations)

            # Use standardized error code for safety violations (Issue #104)
            if HAS_ERROR_CODES:
                # Check if this is a destructive command (safety violation)
                if any(
                    "destructive" in v.lower() or "dangerous" in v.lower()
                    for v in result["safety_check"]["violations"]
                ):
                    error_info = ErrorResponse.create(
                        ErrorRegistry.S401_DESTRUCTIVE_CMD,
                        context={
                            "tool_name": tool_name,
                            "violations": result["safety_check"]["violations"],
                        },
                        hook_name="pre-tool-use",
                    )
                    # Merge error code info into response
                    response["code"] = error_info["code"]
                    response["help_url"] = error_info["help_url"]
                    response["recovery"] = error_info["recovery"]

            print(f"🚫 Tool execution blocked: {tool_name}", file=sys.stderr)
            for violation in result["safety_check"]["violations"]:
                print(f"   - {violation}", file=sys.stderr)
        else:
            # Output warnings and recommendations to stderr for visibility
            if result["warnings"]:
                for warning in result["warnings"]:
                    print(f"⚠️  {warning}", file=sys.stderr)

            if result["recommendations"]:
                for recommendation in result["recommendations"]:
                    print(f"💡 {recommendation}", file=sys.stderr)

            if result["coordination"].get("conflicts"):
                for conflict in result["coordination"]["conflicts"]:
                    print(f"🔄 {conflict}", file=sys.stderr)

            print(f"✅ Tool {tool_name} approved for execution", file=sys.stderr)

        # Output JSON response to stdout
        print(json.dumps(response))

    except json.JSONDecodeError as e:
        # Use standardized error response if available (Issue #104)
        if HAS_ERROR_CODES:
            response = ErrorResponse.create(
                ErrorRegistry.E001_JSON_PARSE,
                context={
                    "parse_error": str(e),
                    "line": getattr(e, "lineno", None),
                    "column": getattr(e, "colno", None),
                },
                hook_name="pre-tool-use",
            )
            response["decision"] = "block"  # Add hook-specific field
        else:
            # Fallback to legacy format
            response = {"error": f"Invalid JSON input: {e}", "decision": "block"}
        print(json.dumps(response))
        sys.exit(1)
    except Exception as e:
        # Generic exception - approve to allow graceful degradation
        # Only block when safety violations are detected (handled above)
        response = {"error": str(e), "decision": "approve"}
        print(json.dumps(response))
        sys.exit(0)  # Don't block on errors


if __name__ == "__main__":
    main()
