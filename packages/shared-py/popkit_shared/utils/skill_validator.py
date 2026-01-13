"""
Skill format validator for PopKit plugin testing.

Validates that skills follow the SKILL.md format with proper frontmatter and structure.
"""

import re
from pathlib import Path
from typing import Any, Dict, List

import yaml


def validate_skill_format(skill_file: Path) -> Dict[str, Any]:
    """
    Validate that a skill file follows the SKILL.md format.

    Args:
        skill_file: Path to SKILL.md file

    Returns:
        Validation result dictionary
    """
    result = {
        "valid": False,
        "file": str(skill_file),
        "has_frontmatter": False,
        "frontmatter": {},
        "has_h1": False,
        "sections": [],
        "errors": [],
        "warnings": [],
    }

    if not skill_file.exists():
        result["errors"].append(f"File not found: {skill_file}")
        return result

    try:
        content = skill_file.read_text(encoding="utf-8")
    except Exception as e:
        result["errors"].append(f"Failed to read file: {e}")
        return result

    # Extract frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)

    if not frontmatter_match:
        result["errors"].append("Missing YAML frontmatter (must start with ---)")
        return result

    result["has_frontmatter"] = True
    frontmatter_text = frontmatter_match.group(1)

    # Parse frontmatter YAML
    try:
        result["frontmatter"] = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        result["errors"].append(f"Invalid YAML in frontmatter: {e}")
        return result

    # Check required frontmatter fields
    if "name" not in result["frontmatter"]:
        result["errors"].append("Frontmatter missing required field: name")
    if "description" not in result["frontmatter"]:
        result["errors"].append("Frontmatter missing required field: description")

    # Extract content after frontmatter
    content_after_fm = content[frontmatter_match.end() :]

    # Check for H1 heading
    h1_match = re.search(r"^# (.+)$", content_after_fm, re.MULTILINE)
    if h1_match:
        result["has_h1"] = True
    else:
        result["warnings"].append("No H1 heading found")

    # Extract sections
    sections = re.findall(r"^## (.+)$", content_after_fm, re.MULTILINE)
    result["sections"] = sections

    # Check for common sections
    common_sections = {"Overview", "When to Use", "Process", "Integration", "Arguments"}
    found_sections = set(sections)
    section_count = len(found_sections & common_sections)

    if section_count < 2:
        result["warnings"].append(
            f"Only {section_count} standard sections found (expected at least 2)"
        )

    # Validate skill name format
    if "name" in result["frontmatter"]:
        name = result["frontmatter"]["name"]
        if not re.match(r"^[a-z0-9-:]+$", name):
            result["errors"].append(
                f"Invalid skill name format: {name} (should be lowercase with hyphens)"
            )

        # Check if directory name matches skill name
        if skill_file.name == "SKILL.md":
            dir_name = skill_file.parent.name
            expected_name = name.replace(":", "-")  # Allow namespace separator
            if dir_name != expected_name and not dir_name.startswith(expected_name):
                result["warnings"].append(
                    f"Directory name '{dir_name}' doesn't match skill name '{name}'"
                )

    # Validate description
    if "description" in result["frontmatter"]:
        desc = result["frontmatter"]["description"]
        if len(desc) < 20:
            result["warnings"].append(f"Description is very short ({len(desc)} chars)")
        if len(desc) > 200:
            result["warnings"].append(f"Description is very long ({len(desc)} chars)")
        if any(word in desc.lower() for word in ["todo", "tbd", "placeholder"]):
            result["errors"].append("Description contains placeholder text")

    # Check for hardcoded paths
    user_path_patterns = [r"/Users/[^/\s]+/", r"C:\\Users\\[^\\s]+\\", r"/home/[^/\s]+/"]

    for pattern in user_path_patterns:
        if re.search(pattern, content_after_fm):
            result["errors"].append(f"Contains hardcoded user path (pattern: {pattern})")
            break

    # Determine overall validity
    result["valid"] = len(result["errors"]) == 0

    return result


def validate_all_skills(skill_files: List[Path]) -> List[Dict[str, Any]]:
    """
    Validate all skill files.

    Args:
        skill_files: List of paths to SKILL.md files

    Returns:
        List of validation results
    """
    return [validate_skill_format(skill_file) for skill_file in skill_files]


def get_skill_statistics(skills_dir: Path) -> Dict[str, Any]:
    """
    Get statistics about skills in a directory.

    Args:
        skills_dir: Path to skills directory

    Returns:
        Statistics dictionary
    """
    stats = {
        "total_skills": 0,
        "valid_skills": 0,
        "invalid_skills": 0,
        "missing_name": 0,
        "missing_description": 0,
        "missing_sections": 0,
        "total_errors": 0,
        "total_warnings": 0,
    }

    if not skills_dir.exists():
        return stats

    skill_files = list(skills_dir.glob("*/SKILL.md"))
    stats["total_skills"] = len(skill_files)

    for skill_file in skill_files:
        result = validate_skill_format(skill_file)

        if result["valid"]:
            stats["valid_skills"] += 1
        else:
            stats["invalid_skills"] += 1

        if "name" not in result["frontmatter"]:
            stats["missing_name"] += 1
        if "description" not in result["frontmatter"]:
            stats["missing_description"] += 1
        if len(result["sections"]) < 2:
            stats["missing_sections"] += 1

        stats["total_errors"] += len(result["errors"])
        stats["total_warnings"] += len(result["warnings"])

    return stats


def check_skill_naming_consistency(skills_dir: Path) -> Dict[str, Any]:
    """
    Check that skill names are consistent across directory and frontmatter.

    Args:
        skills_dir: Path to skills directory

    Returns:
        Consistency check results
    """
    result = {"total_skills": 0, "consistent": 0, "inconsistent": 0, "issues": []}

    if not skills_dir.exists():
        return result

    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
    result["total_skills"] = len(skill_dirs)

    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            result["issues"].append({"directory": skill_dir.name, "issue": "Missing SKILL.md file"})
            result["inconsistent"] += 1
            continue

        validation = validate_skill_format(skill_file)

        if "name" not in validation["frontmatter"]:
            result["issues"].append(
                {"directory": skill_dir.name, "issue": "Missing name in frontmatter"}
            )
            result["inconsistent"] += 1
            continue

        skill_name = validation["frontmatter"]["name"]
        expected_dir = skill_name.replace(":", "-")

        if skill_dir.name != expected_dir:
            result["issues"].append(
                {
                    "directory": skill_dir.name,
                    "frontmatter_name": skill_name,
                    "expected_directory": expected_dir,
                    "issue": "Directory name does not match skill name",
                }
            )
            result["inconsistent"] += 1
        else:
            result["consistent"] += 1

    return result


def find_duplicate_skill_names(skills_dir: Path) -> Dict[str, List[str]]:
    """
    Find skills with duplicate names.

    Args:
        skills_dir: Path to skills directory

    Returns:
        Dictionary mapping duplicate names to list of directories
    """
    name_to_dirs = {}

    if not skills_dir.exists():
        return {}

    for skill_file in skills_dir.glob("*/SKILL.md"):
        validation = validate_skill_format(skill_file)

        if "name" in validation["frontmatter"]:
            name = validation["frontmatter"]["name"]
            dir_name = skill_file.parent.name

            if name not in name_to_dirs:
                name_to_dirs[name] = []
            name_to_dirs[name].append(dir_name)

    # Return only duplicates
    return {name: dirs for name, dirs in name_to_dirs.items() if len(dirs) > 1}
