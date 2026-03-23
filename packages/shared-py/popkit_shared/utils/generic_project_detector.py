#!/usr/bin/env python3
"""
Generic Project Type Detector for PopKit Routines.

Detects project type, package manager, testing framework, and build tools
to enable generic morning/nightly routines that work with any workspace.

Issue #69: Generic Workspace Routine Templates
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .tech_stack_detector import Technology, TechnologyType, TechStackDetector

    HAS_TECH_STACK_DETECTOR = True
except ImportError:
    HAS_TECH_STACK_DETECTOR = False


@dataclass
class ProjectType:
    """Detected project type with relevant tools."""

    primary_language: str  # e.g., "Python", "JavaScript", "Rust"
    package_manager: str | None = None  # e.g., "npm", "pip", "cargo"
    test_framework: str | None = None  # e.g., "jest", "pytest", "cargo test"
    build_tool: str | None = None  # e.g., "npm run build", "cargo build"
    linter: str | None = None  # e.g., "eslint", "ruff", "clippy"
    formatter: str | None = None  # e.g., "prettier", "ruff", "rustfmt"

    # Common service ports based on tech stack
    expected_services: list[dict[str, Any]] = None  # e.g., [{"name": "dev server", "port": 3000}]

    # Dependency check commands
    check_installed: str | None = None  # e.g., "npm list" or "pip freeze"
    check_outdated: str | None = None  # e.g., "npm outdated" or "pip list --outdated"
    install_command: str | None = None  # e.g., "npm install" or "pip install -r requirements.txt"


class GenericProjectDetector:
    """
    Detects project type and provides workspace-appropriate commands.

    Supports:
    - Node.js (npm, pnpm, yarn)
    - Python (pip, poetry, pipenv)
    - Rust (cargo)
    - Go (go modules)
    - Ruby (bundler)
    - Java (maven, gradle)
    - .NET (dotnet)
    """

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self._project_type: ProjectType | None = None

    def detect(self) -> ProjectType:
        """
        Detect project type and tools.

        Returns:
            ProjectType with detected language, tools, and commands
        """
        if self._project_type is not None:
            return self._project_type

        if not HAS_TECH_STACK_DETECTOR:
            # Fallback: basic file-based detection
            return self._detect_fallback()

        # Use tech_stack_detector for comprehensive detection
        detector = TechStackDetector(str(self.project_path))
        tech_stack = detector.detect_all()

        # Extract primary language
        primary_language = tech_stack.primary_language or "Unknown"

        # Extract relevant technologies
        package_manager = self._find_tech(tech_stack.technologies, TechnologyType.PACKAGE_MANAGER)
        test_framework = self._find_tech(tech_stack.technologies, TechnologyType.TESTING_FRAMEWORK)
        build_tool = self._find_tech(tech_stack.technologies, TechnologyType.BUILD_TOOL)
        linter = self._find_tech(tech_stack.technologies, TechnologyType.LINTER)
        formatter = self._find_tech(tech_stack.technologies, TechnologyType.FORMATTER)

        # Build ProjectType with language-specific defaults
        self._project_type = self._build_project_type(
            primary_language, package_manager, test_framework, build_tool, linter, formatter
        )

        return self._project_type

    def _find_tech(self, technologies: list[Technology], tech_type: TechnologyType) -> str | None:
        """Find first technology of given type."""
        for tech in technologies:
            if tech.type == tech_type:
                return tech.name
        return None

    def _build_project_type(
        self,
        language: str,
        package_manager: str | None,
        test_framework: str | None,
        build_tool: str | None,
        linter: str | None,
        formatter: str | None,
    ) -> ProjectType:
        """Build ProjectType with language-specific defaults."""

        # Node.js / JavaScript / TypeScript
        if language in ("JavaScript", "TypeScript"):
            pm = package_manager or "npm"
            return ProjectType(
                primary_language=language,
                package_manager=pm,
                test_framework=test_framework or "jest",
                build_tool=build_tool or f"{pm} run build",
                linter=linter or "eslint",
                formatter=formatter or "prettier",
                expected_services=[
                    {"name": "dev server", "port": 3000, "description": "Development server"},
                    {"name": "api", "port": 8000, "description": "API server (if separate)"},
                ],
                check_installed=f"{pm} list --depth=0",
                check_outdated=f"{pm} outdated",
                install_command=f"{pm} install",
            )

        # Python
        elif language == "Python":
            pm = package_manager or "pip"
            return ProjectType(
                primary_language=language,
                package_manager=pm,
                test_framework=test_framework or "pytest",
                build_tool=None,  # Python typically doesn't need build
                linter=linter or "ruff",
                formatter=formatter or "ruff",
                expected_services=[
                    {"name": "api", "port": 8000, "description": "Python API server"},
                    {"name": "database", "port": 5432, "description": "PostgreSQL"},
                ],
                check_installed=f"{pm} freeze" if pm == "pip" else f"{pm} list",
                check_outdated=f"{pm} list --outdated" if pm == "pip" else f"{pm} show --outdated",
                install_command=f"{pm} install -r requirements.txt"
                if pm == "pip"
                else f"{pm} install",
            )

        # Rust
        elif language == "Rust":
            return ProjectType(
                primary_language=language,
                package_manager="cargo",
                test_framework="cargo test",
                build_tool="cargo build",
                linter="clippy",
                formatter="rustfmt",
                expected_services=[],  # Rust services vary widely
                check_installed="cargo tree --depth=1",
                check_outdated="cargo outdated",
                install_command="cargo build",
            )

        # Go
        elif language == "Go":
            return ProjectType(
                primary_language=language,
                package_manager="go mod",
                test_framework="go test",
                build_tool="go build",
                linter="golangci-lint",
                formatter="gofmt",
                expected_services=[{"name": "api", "port": 8080, "description": "Go API server"}],
                check_installed="go list -m all",
                check_outdated="go list -u -m all",
                install_command="go mod download",
            )

        # Ruby
        elif language == "Ruby":
            return ProjectType(
                primary_language=language,
                package_manager="bundler",
                test_framework="rspec",
                build_tool=None,
                linter="rubocop",
                formatter="rubocop",
                expected_services=[{"name": "rails", "port": 3000, "description": "Rails server"}],
                check_installed="bundle list",
                check_outdated="bundle outdated",
                install_command="bundle install",
            )

        # Java
        elif language == "Java":
            pm = package_manager or "maven"
            return ProjectType(
                primary_language=language,
                package_manager=pm,
                test_framework="JUnit",
                build_tool="mvn package" if pm == "maven" else "gradle build",
                linter=None,
                formatter=None,
                expected_services=[
                    {"name": "spring boot", "port": 8080, "description": "Spring Boot application"}
                ],
                check_installed=f"{pm} dependency:list" if pm == "maven" else f"{pm} dependencies",
                check_outdated=f"{pm} versions:display-dependency-updates"
                if pm == "maven"
                else f"{pm} dependencyUpdates",
                install_command=f"{pm} install" if pm == "maven" else f"{pm} build",
            )

        # .NET
        elif language == ".NET":
            return ProjectType(
                primary_language=language,
                package_manager="dotnet",
                test_framework="xUnit",
                build_tool="dotnet build",
                linter=None,
                formatter=None,
                expected_services=[
                    {"name": "asp.net", "port": 5000, "description": "ASP.NET application"}
                ],
                check_installed="dotnet list package",
                check_outdated="dotnet list package --outdated",
                install_command="dotnet restore",
            )

        # Unknown / Generic
        else:
            return ProjectType(
                primary_language=language,
                package_manager=None,
                test_framework=None,
                build_tool=None,
                linter=None,
                formatter=None,
                expected_services=[],
                check_installed=None,
                check_outdated=None,
                install_command=None,
            )

    def _detect_fallback(self) -> ProjectType:
        """
        Fallback detection when tech_stack_detector is not available.

        Uses simple file existence checks.
        """
        # Check for Node.js
        if (self.project_path / "package.json").exists():
            pm = (
                "pnpm"
                if (self.project_path / "pnpm-lock.yaml").exists()
                else "yarn"
                if (self.project_path / "yarn.lock").exists()
                else "npm"
            )
            return self._build_project_type("JavaScript", pm, None, None, None, None)

        # Check for Python
        if (self.project_path / "requirements.txt").exists() or (
            self.project_path / "pyproject.toml"
        ).exists():
            pm = "poetry" if (self.project_path / "poetry.lock").exists() else "pip"
            return self._build_project_type("Python", pm, None, None, None, None)

        # Check for Rust
        if (self.project_path / "Cargo.toml").exists():
            return self._build_project_type("Rust", "cargo", None, None, None, None)

        # Check for Go
        if (self.project_path / "go.mod").exists():
            return self._build_project_type("Go", "go mod", None, None, None, None)

        # Check for Ruby
        if (self.project_path / "Gemfile").exists():
            return self._build_project_type("Ruby", "bundler", None, None, None, None)

        # Check for Java
        if (self.project_path / "pom.xml").exists():
            return self._build_project_type("Java", "maven", None, None, None, None)
        if (self.project_path / "build.gradle").exists():
            return self._build_project_type("Java", "gradle", None, None, None, None)

        # Check for .NET
        if list(self.project_path.glob("*.csproj")):
            return self._build_project_type(".NET", "dotnet", None, None, None, None)

        # Unknown project type
        return ProjectType(primary_language="Unknown")


def detect_project_type(project_path: str = ".") -> ProjectType:
    """
    Convenience function to detect project type.

    Args:
        project_path: Path to project directory

    Returns:
        ProjectType with detected language and tools

    Example:
        >>> project = detect_project_type()
        >>> print(f"Language: {project.primary_language}")
        >>> print(f"Package Manager: {project.package_manager}")
        >>> print(f"Check outdated: {project.check_outdated}")
    """
    detector = GenericProjectDetector(project_path)
    return detector.detect()
