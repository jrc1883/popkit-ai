"""Cross-plugin validators for PopKit ecosystem testing."""

from .ecosystem_validators import (
    validate_agent_count_matches,
    validate_namespace_consistent,
    validate_no_circular_deps,
    validate_semver_valid,
    validate_shared_package_version,
    validate_skill_naming_convention,
    validate_total_agents,
    validate_unique_agent_names,
    validate_unique_command_names,
    validate_unique_skill_names,
    validate_version_compatibility,
)

__all__ = [
    "validate_unique_command_names",
    "validate_unique_skill_names",
    "validate_unique_agent_names",
    "validate_namespace_consistent",
    "validate_skill_naming_convention",
    "validate_semver_valid",
    "validate_version_compatibility",
    "validate_shared_package_version",
    "validate_no_circular_deps",
    "validate_agent_count_matches",
    "validate_total_agents",
]
