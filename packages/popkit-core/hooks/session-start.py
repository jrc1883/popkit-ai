#!/usr/bin/env python3
"""
Session Start Hook
Handles session initialization, setup, and update notifications.

Responsibilities:
1. Log session start
2. Check for PopKit updates
3. Register project with PopKit Cloud (async, non-blocking)
4. Ensure PopKit directories exist (auto-init)
5. Filter agents based on initial task (Phase 2: Embedding-Based Agent Loading)
6. Detect and optimize for agent_type when --agent flag is used (Claude Code 2.1.2+)
"""

import sys
import json
import os
import threading
from pathlib import Path
from datetime import datetime

# Import version check utility
try:
    from popkit_shared.utils.version import (
        check_for_updates,
        format_update_notification,
        get_current_version,
    )

    HAS_VERSION_CHECK = True
except ImportError:
    HAS_VERSION_CHECK = False

# Import error code system (Issue #104)
try:
    from popkit_shared.utils.error_codes import ErrorRegistry, ErrorResponse

    HAS_ERROR_CODES = True
except ImportError:
    HAS_ERROR_CODES = False

# Import project registration client
try:
    from popkit_shared.utils.project_client import ProjectClient, ProjectRegistration

    HAS_PROJECT_CLIENT = True
except ImportError:
    HAS_PROJECT_CLIENT = False

# Import agent loader for semantic filtering (Phase 2)
try:
    from agent_loader import AgentLoader

    HAS_AGENT_LOADER = True
except ImportError:
    HAS_AGENT_LOADER = False

# Import XML context generation utilities (Phase 1: XML Integration)
try:
    from context_state import clear_context_state, save_context_state, compute_hash
    from xml_generator import generate_project_context_xml

    HAS_XML_CONTEXT = True
except ImportError:
    HAS_XML_CONTEXT = False


def create_logs_directory():
    """Create logs directory if it doesn't exist."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def log_session_start(data):
    """Log session start data to JSON file."""
    logs_dir = create_logs_directory()
    log_file = logs_dir / "session_start.json"

    # Add timestamp
    data["timestamp"] = datetime.now().isoformat()

    # Read existing log data
    log_data = []
    if log_file.exists():
        try:
            with open(log_file, "r") as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            log_data = []

    # Append new data
    log_data.append(data)

    # Write updated log
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)


def check_plugin_updates():
    """Check for popkit updates and display notification if available.

    This is non-blocking - any errors are silently ignored.
    """
    if not HAS_VERSION_CHECK:
        return None

    try:
        has_update, release_info = check_for_updates()

        if has_update and release_info:
            current = get_current_version()
            notification = format_update_notification(release_info, current)
            print(notification, file=sys.stderr)

            return {
                "update_available": True,
                "current_version": current,
                "latest_version": release_info.get("version"),
                "release_url": release_info.get("url"),
            }
    except Exception:
        pass  # Silent failure - never block session start

    return None


def should_attempt_cloud_registration():
    """
    Check circuit breaker - should we attempt cloud registration?

    Circuit breaker prevents repeated failed attempts by tracking:
    - Last failure timestamp
    - Consecutive failure count

    Skip registration if we failed within last 5 minutes.

    Returns:
        bool: True if we should attempt, False if circuit is open
    """
    try:
        circuit_file = Path.home() / ".claude" / "config" / "cloud_circuit.json"

        if not circuit_file.exists():
            return True  # No failures yet, try it

        with open(circuit_file, "r") as f:
            circuit_data = json.load(f)

        last_failure = circuit_data.get("last_failure")
        if not last_failure:
            return True

        # Parse timestamp
        from datetime import datetime, timedelta

        last_failure_time = datetime.fromisoformat(last_failure)
        cooldown_period = timedelta(minutes=5)

        # Check if cooldown period has passed
        if datetime.now() - last_failure_time < cooldown_period:
            return False  # Circuit open - don't retry yet

        return True  # Cooldown passed, try again

    except Exception:
        return True  # On error, allow attempt


def record_cloud_registration_failure():
    """Record a cloud registration failure for circuit breaker."""
    try:
        circuit_dir = Path.home() / ".claude" / "config"
        circuit_dir.mkdir(parents=True, exist_ok=True)
        circuit_file = circuit_dir / "cloud_circuit.json"

        # Load existing data
        circuit_data = {}
        if circuit_file.exists():
            try:
                with open(circuit_file, "r") as f:
                    circuit_data = json.load(f)
            except json.JSONDecodeError:
                circuit_data = {}

        # Update failure info
        circuit_data["last_failure"] = datetime.now().isoformat()
        circuit_data["failure_count"] = circuit_data.get("failure_count", 0) + 1

        # Write back
        with open(circuit_file, "w") as f:
            json.dump(circuit_data, f, indent=2)

    except Exception:
        pass  # Silent failure


def record_cloud_registration_success():
    """Record a successful cloud registration - reset circuit breaker."""
    try:
        circuit_file = Path.home() / ".claude" / "config" / "cloud_circuit.json"
        if circuit_file.exists():
            circuit_file.unlink()  # Remove circuit breaker file on success
    except Exception:
        pass  # Silent failure


def _register_project_sync():
    """
    Synchronous project registration (runs in background thread).

    This is the actual registration logic that talks to PopKit Cloud.
    """
    if not HAS_PROJECT_CLIENT:
        return None

    try:
        # Check circuit breaker first
        if not should_attempt_cloud_registration():
            return None  # Circuit open - skip registration

        client = ProjectClient()

        if not client.is_available:
            return None

        result = client.register_project()

        if result:
            record_cloud_registration_success()  # Reset circuit breaker
            print(
                f"Project registered with PopKit Cloud (session #{result.session_count})",
                file=sys.stderr,
            )
            return {
                "project_id": result.project_id,
                "session_count": result.session_count,
                "status": result.status,
            }
        else:
            record_cloud_registration_failure()

    except Exception:
        record_cloud_registration_failure()  # Track failure
        pass  # Silent failure - never block session start

    return None


def register_project_async():
    """
    Register project with PopKit Cloud asynchronously (non-blocking).

    Launches registration in a background thread and returns immediately.
    This ensures session-start hook completes quickly without waiting for network.

    Returns:
        dict: Status indicating async registration was started
    """
    if not HAS_PROJECT_CLIENT:
        return None

    try:
        # Launch registration in background thread (daemon=True means it won't block process exit)
        thread = threading.Thread(target=_register_project_sync, daemon=True)
        thread.start()

        return {
            "status": "async",
            "message": "Cloud registration started in background",
        }

    except Exception:
        return None


def ensure_popkit_directories():
    """Ensure PopKit runtime directories exist.

    This is idempotent and fast - creates directories only if missing.
    Part of the skill automation architecture (Issue #173).

    Created directories:
    - .claude/popkit/           - PopKit runtime state
    - .claude/popkit/routines/  - Custom morning/nightly routines

    Returns:
        dict: Status of directory creation, or None on error
    """
    try:
        cwd = Path(os.getcwd())

        # Skip if not in a git repo or project directory
        # (Don't auto-create in random directories)
        if not (cwd / ".git").exists() and not (cwd / "CLAUDE.md").exists():
            return None

        base = cwd / ".claude" / "popkit"
        dirs_to_create = [
            base,
            base / "routines" / "morning",
            base / "routines" / "nightly",
        ]

        created = []
        for d in dirs_to_create:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                created.append(str(d.relative_to(cwd)))

                # Add .gitkeep for empty directories
                gitkeep = d / ".gitkeep"
                if not gitkeep.exists():
                    gitkeep.touch()

        # Create config.json if missing
        config_path = base / "config.json"
        config_created = False
        if not config_path.exists() and base.exists():
            project_name = cwd.name

            # Generate prefix from project name
            words = project_name.replace("-", " ").replace("_", " ").split()
            if len(words) == 1:
                prefix = words[0][:2].lower()
            else:
                prefix = "".join(word[0].lower() for word in words[:3])

            config = {
                "version": "1.0",
                "project_name": project_name,
                "project_prefix": prefix,
                "default_routines": {"morning": "pk", "nightly": "pk"},
                "initialized_at": datetime.now().isoformat(),
                "popkit_version": "1.2.0",
                "tier": "free",
                "features": {
                    "power_mode": "not_configured",
                    "deployments": [],
                    "custom_routines": [],
                },
            }

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            config_created = True

        if created or config_created:
            return {"directories_created": created, "config_created": config_created}

        return None  # Nothing needed

    except Exception:
        pass  # Silent failure - never block session start

    return None


def ensure_pattern_learner_directories():
    """Ensure pattern learner and research directories exist.

    Creates directories for the three-tier learning system:
    - Tier 1 (Global): ~/.claude/config/ for command patterns database
    - Tier 2 (Project): .claude/research/ for project research index
    - Tier 3 (Project): .claude/expertise/ for agent expertise files

    Part of Agent Expertise System (Issue #201, Phase 1).

    Returns:
        dict: Status of directory creation, or None on error
    """
    try:
        home = Path.home()
        cwd = Path(os.getcwd())

        # Global config directory (Tier 1)
        global_config = home / ".claude" / "config"

        # Project-specific directories (Tier 2 and 3)
        project_research = cwd / ".claude" / "research"
        project_expertise = cwd / ".claude" / "expertise"

        dirs_to_create = [
            global_config,
            project_research,
            project_research / "entries",
            project_expertise,
        ]

        created = []
        for d in dirs_to_create:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                # Use relative path for project dirs, absolute for global
                try:
                    if d.is_relative_to(cwd):
                        created.append(str(d.relative_to(cwd)))
                    else:
                        created.append(str(d))
                except (ValueError, TypeError):
                    # is_relative_to may fail on some Python versions
                    created.append(str(d))

        # Initialize research index if missing
        index_path = project_research / "index.json"
        index_created = False
        if not index_path.exists() and project_research.exists():
            # Create minimal research index structure
            index_data = {
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "entries": [],
                "tags": {},
                "metadata": {
                    "total_entries": 0,
                    "entry_types": {
                        "decision": 0,
                        "finding": 0,
                        "learning": 0,
                        "spike": 0,
                    },
                },
            }
            with open(index_path, "w") as f:
                json.dump(index_data, f, indent=2)
            index_created = True

        if created or index_created:
            return {"directories_created": created, "index_created": index_created}

        return None  # Nothing needed

    except Exception:
        pass  # Silent failure - never block session start

    return None


def load_agent_expertise():
    """Load expertise files for relevant agents.

    This is non-blocking - any errors are silently ignored.

    Part of Agent Expertise System (Issue #201, Phase 2).

    Returns:
        dict: Loaded expertise info, or None on error
    """
    try:
        # Import here to avoid circular dependencies
        from popkit_shared.utils.expertise_manager import ExpertiseManager

        cwd = Path(os.getcwd())
        expertise_dir = cwd / ".claude" / "expertise"

        if not expertise_dir.exists():
            return None

        loaded = []
        for agent_dir in expertise_dir.iterdir():
            if agent_dir.is_dir():
                expertise_file = agent_dir / "expertise.yaml"
                if expertise_file.exists():
                    agent_id = agent_dir.name
                    manager = ExpertiseManager(agent_id, cwd)
                    summary = manager.get_summary()
                    loaded.append(
                        {
                            "agent_id": agent_id,
                            "patterns": summary["total_patterns"],
                            "preferences": summary["total_preferences"],
                        }
                    )

        if loaded:
            print(f"Agent expertise loaded: {len(loaded)} agents", file=sys.stderr)
            return {"agents": loaded}

        return None

    except Exception:
        pass  # Silent failure

    return None


def load_relevant_agents_for_session(data):
    """Load relevant agents based on initial user message.

    Part of Phase 2: Embedding-Based Agent Loading.
    This is non-blocking - any errors are silently ignored.

    Args:
        data: Session input data

    Returns:
        dict: Agent loading info, or None on error
    """
    if not HAS_AGENT_LOADER:
        return None

    try:
        # Get initial user message (if available)
        messages = data.get("messages", [])
        user_message = next((m["content"] for m in messages if m["role"] == "user"), "")

        # If no user message yet, skip agent filtering
        if not user_message:
            return None

        # Load relevant agents
        loader = AgentLoader()
        relevant_agents = loader.load(user_message, top_k=10)

        # Output debug info to stderr
        agent_ids = [a["agent_id"] for a in relevant_agents]
        print(
            f"Agent filtering: loaded {len(agent_ids)} relevant agents", file=sys.stderr
        )
        print(
            f"  Agents: {', '.join(agent_ids[:5])}{'...' if len(agent_ids) > 5 else ''}",
            file=sys.stderr,
        )

        return {
            "loaded_agents": agent_ids,
            "agent_count": len(relevant_agents),
            "query_preview": user_message[:100],
        }
    except Exception:
        pass  # Silent failure - never block session start

    return None


def detect_project_context():
    """Detect project context for XML generation.

    Analyzes the current project to extract:
    - Project name
    - Tech stack (from package.json dependencies)
    - Infrastructure (future: detect from configs)
    - Current work (git branch, recent issues)

    Returns:
        dict: Project context with stack, infrastructure, current_work
    """
    try:
        cwd = Path(os.getcwd())
        context = {
            "name": cwd.name,
            "stack": [],
            "infrastructure": {},
            "current_work": {},
        }

        # Detect stack from package.json
        package_json = cwd / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    pkg = json.load(f)
                    deps = {
                        **pkg.get("dependencies", {}),
                        **pkg.get("devDependencies", {}),
                    }

                    # Detect frameworks
                    if "next" in deps:
                        context["stack"].append("Next.js")
                    if "react" in deps and "next" not in deps:
                        context["stack"].append("React")
                    if "vue" in deps:
                        context["stack"].append("Vue")
                    if "express" in deps:
                        context["stack"].append("Express")
                    if "@supabase/supabase-js" in deps:
                        context["stack"].append("Supabase")
                    if "fastapi" in " ".join(deps.keys()).lower():
                        context["stack"].append("FastAPI")

            except (json.JSONDecodeError, IOError):
                pass

        # Detect Python stack from requirements.txt
        requirements_txt = cwd / "requirements.txt"
        if requirements_txt.exists():
            try:
                with open(requirements_txt, "r") as f:
                    requirements = f.read().lower()
                    if "fastapi" in requirements:
                        context["stack"].append("FastAPI")
                    if "django" in requirements:
                        context["stack"].append("Django")
                    if "flask" in requirements:
                        context["stack"].append("Flask")
            except IOError:
                # Ignore file read errors - requirements.txt is optional context
                pass

        # Detect current branch
        try:
            import subprocess

            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=1,
                cwd=cwd,
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                if branch:
                    context["current_work"]["branch"] = branch
        except Exception:
            # Ignore git command errors - branch detection is optional context
            pass

        return context

    except Exception:
        return {
            "name": "unknown",
            "stack": [],
            "infrastructure": {},
            "current_work": {},
        }


# Import agent type detection from helpers module
from session_start_helpers import detect_agent_type_session


def main():
    """Main entry point for the hook - JSON stdin/stdout protocol"""
    try:
        # Read input data from stdin
        input_data = sys.stdin.read()
        data = json.loads(input_data) if input_data.strip() else {}

        # Skip expensive network operations in test mode
        test_mode = os.environ.get("POPKIT_TEST_MODE") == "true"

        # Log the session start
        log_session_start(data)

        # Check for updates (non-blocking, skip in test mode)
        update_info = None if test_mode else check_plugin_updates()

        # Register project with PopKit Cloud (async, non-blocking, skip in test mode)
        project_info = None if test_mode else register_project_async()

        # Ensure PopKit directories exist (auto-init, non-blocking)
        popkit_init = ensure_popkit_directories()
        if popkit_init:
            dirs = popkit_init.get("directories_created", [])
            config = popkit_init.get("config_created", False)
            if dirs or config:
                parts = []
                if dirs:
                    parts.append(f"directories: {len(dirs)}")
                if config:
                    parts.append("config.json")
                print(f"PopKit auto-init: {', '.join(parts)}", file=sys.stderr)

        # Ensure pattern learner and research directories (Issue #201, Phase 1)
        learning_init = ensure_pattern_learner_directories()
        if learning_init:
            dirs = learning_init.get("directories_created", [])
            index = learning_init.get("index_created", False)
            if dirs or index:
                parts = []
                if dirs:
                    parts.append(f"directories: {len(dirs)}")
                if index:
                    parts.append("research index")
                print(
                    f"Learning systems initialized: {', '.join(parts)}", file=sys.stderr
                )

        # Load agent expertise files (Issue #201, Phase 2, non-blocking)
        expertise_loading = load_agent_expertise()

        # Detect agent_type from --agent flag (Claude Code 2.1.2+)
        agent_type_info = detect_agent_type_session(data)

        # Set POPKIT_ACTIVE_AGENT for expertise tracking (Issue #80)
        if agent_type_info and agent_type_info.get("agent_type"):
            agent_type = agent_type_info["agent_type"]
            os.environ["POPKIT_ACTIVE_AGENT"] = agent_type
            print(f"  Set POPKIT_ACTIVE_AGENT={agent_type}", file=sys.stderr)

        # Load relevant agents for this session (Phase 2, non-blocking)
        # Skip embedding-based filtering if agent_type is specified (user already selected agent)
        agent_loading = None
        if agent_type_info and agent_type_info.get("skip_embedding_filter"):
            # Agent already selected via --agent flag, skip embedding-based filtering
            print("  Skipping embedding filter (agent pre-selected)", file=sys.stderr)
        else:
            # Normal session - use embedding-based agent filtering
            agent_loading = load_relevant_agents_for_session(data)

        # Generate initial XML context and save state (Phase 1: XML Integration)
        xml_context_info = None
        if HAS_XML_CONTEXT:
            try:
                # Get session ID from data
                session_id = data.get("session_id", "default")

                # Clear previous session state
                clear_context_state(session_id)

                # Detect project context
                project_context = detect_project_context()

                # Generate XML
                xml_output = generate_project_context_xml(project_context)

                # Save initial state
                initial_state = {
                    "context_sent": {
                        "project": {
                            "hash": compute_hash(project_context),
                            "sent_at_message": 0,  # Session start, before first message
                        }
                    },
                    "message_count": 0,
                    "last_full_context_message": 0,
                }
                save_context_state(session_id, initial_state)

                # Print XML to stderr for visibility
                print("\n--- Project Context (XML) ---", file=sys.stderr)
                print(xml_output, file=sys.stderr)
                print("--- End Project Context ---\n", file=sys.stderr)

                xml_context_info = {
                    "xml_generated": True,
                    "state_saved": True,
                    "project_name": project_context.get("name"),
                }

            except Exception as e:
                # Silent failure - don't block session start
                print(f"Warning: XML context generation failed: {e}", file=sys.stderr)

        # Print welcome message to stderr
        print("Session started - hooks system active", file=sys.stderr)

        # Output JSON response to stdout
        response = {
            "status": "success",
            "message": "Session started - hooks system active",
            "timestamp": datetime.now().isoformat(),
            "session_data": data,
        }

        # Include update info if available
        if update_info:
            response["update_check"] = update_info

        # Include project registration info if available
        if project_info:
            response["project_registration"] = project_info

        # Include popkit init info if directories were created
        if popkit_init:
            response["popkit_init"] = popkit_init

        # Include learning systems init info if directories were created (Issue #201)
        if learning_init:
            response["learning_init"] = learning_init

        # Include expertise loading info if available (Issue #201, Phase 2)
        if expertise_loading:
            response["expertise_loading"] = expertise_loading

        # Include agent loading info if available (Phase 2)
        if agent_loading:
            response["agent_loading"] = agent_loading

        # Include agent_type info if --agent flag was used (Claude Code 2.1.2+)
        if agent_type_info:
            response["agent_type_optimization"] = agent_type_info

        # Include XML context info if generated (Phase 1)
        if xml_context_info:
            response["xml_context"] = xml_context_info

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
                hook_name="session-start",
            )
        else:
            # Fallback to legacy format
            response = {"status": "error", "error": f"Invalid JSON input: {e}"}
        print(json.dumps(response))
        sys.exit(0)  # Don't block on errors
    except Exception as e:
        # Generic exception - graceful degradation (non-blocking)
        # Session-start hook never blocks, even on errors
        response = {"status": "error", "error": str(e)}
        print(json.dumps(response))
        print(f"⚠️ Error in session-start hook: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on errors


if __name__ == "__main__":
    main()
