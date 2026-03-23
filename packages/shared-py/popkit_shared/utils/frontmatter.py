"""Shared YAML frontmatter extraction and project detection utilities.

Centralizes logic previously duplicated across embedding_init.py,
embedding_project.py, and semantic_router.py.
"""

from pathlib import Path


def extract_yaml_frontmatter(content: str) -> dict[str, str]:
    """Extract YAML frontmatter from markdown file.

    Parses the --- delimited frontmatter block at the start of a markdown file
    and returns key-value pairs.

    Args:
        content: Raw markdown file content.

    Returns:
        Dictionary of frontmatter key-value pairs, or empty dict if no frontmatter.
    """
    if not content.startswith("---"):
        return {}

    end = content.find("---", 3)
    if end < 0:
        return {}

    frontmatter = content[3:end].strip()
    result = {}

    for line in frontmatter.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            result[key] = value

    return result


def get_project_root(start_path: str | None = None) -> str | None:
    """Detect project root by looking for .claude/ or .git/ directory.

    Walks up the directory tree from start_path (or cwd) to find the
    nearest project root.

    Args:
        start_path: Starting path (defaults to cwd).

    Returns:
        Project root path or None.
    """
    current = Path(start_path) if start_path else Path.cwd()

    for path in [current] + list(current.parents):
        if (path / ".claude").is_dir():
            return str(path)
        if (path / ".git").is_dir():
            return str(path)

    return None
