#!/usr/bin/env python3
"""
Tech Stack Detection Module

Analyzes project files to identify technologies and their configurations.
Supports detection of:
- Programming languages (Python, JavaScript/TypeScript, Rust, Go, Ruby, Java, C/C++)
- Package managers (npm, pip, cargo, go modules, bundler, maven, gradle)
- Testing frameworks (pytest, jest, mocha, cargo test, go test)
- Linters and formatters (ruff, eslint, prettier, clippy, golangci-lint)
- Databases (PostgreSQL, MySQL, MongoDB, Redis)
- Containerization (Docker, Kubernetes)
"""

import json
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TechnologyType(Enum):
    """Categories of detected technologies."""

    LANGUAGE = "Language"
    PACKAGE_MANAGER = "Package Manager"
    TESTING_FRAMEWORK = "Testing Framework"
    LINTER = "Linter"
    FORMATTER = "Formatter"
    DATABASE = "Database"
    CONTAINERIZATION = "Containerization"
    BUILD_TOOL = "Build Tool"
    OTHER = "Other"


@dataclass
class Technology:
    """Represents a detected technology."""

    name: str
    type: TechnologyType
    confidence: float  # 0.0-1.0
    version: Optional[str] = None
    config_file: Optional[str] = None
    evidence: List[str] = field(default_factory=list)


@dataclass
class TechStack:
    """Complete technology stack analysis."""

    technologies: List[Technology]
    primary_language: Optional[str] = None
    confidence_score: float = 0.0  # Overall confidence
    config_files_found: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TechStackDetector:
    """Detects project technology stack from configuration files."""

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.technologies: List[Technology] = []
        self.config_files: List[str] = []
        self.warnings: List[str] = []

    def _file_exists(self, *path_parts: str) -> bool:
        """Check if file exists in project."""
        file_path = self.project_path / Path(*path_parts)
        exists = file_path.exists()
        if exists:
            self.config_files.append(str(Path(*path_parts)))
        return exists

    def _read_file(self, *path_parts: str) -> Optional[str]:
        """Read file contents safely."""
        try:
            file_path = self.project_path / Path(*path_parts)
            return file_path.read_text(encoding="utf-8")
        except Exception:
            return None

    def _read_json(self, *path_parts: str) -> Optional[Dict[str, Any]]:
        """Read and parse JSON file."""
        content = self._read_file(*path_parts)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                self.warnings.append(f"Invalid JSON in {'/'.join(path_parts)}")
        return None

    def _run_command(self, args: List[str]) -> Optional[str]:
        """Run command and return output."""
        try:
            result = subprocess.run(
                args,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _add_technology(
        self,
        name: str,
        tech_type: TechnologyType,
        confidence: float,
        version: Optional[str] = None,
        config_file: Optional[str] = None,
        evidence: Optional[List[str]] = None,
    ):
        """Add detected technology to list."""
        self.technologies.append(
            Technology(
                name=name,
                type=tech_type,
                confidence=confidence,
                version=version,
                config_file=config_file,
                evidence=evidence or [],
            )
        )

    # ========================================================================
    # Python Detection
    # ========================================================================

    def detect_python(self):
        """Detect Python and related tools."""
        python_detected = False
        evidence = []

        # Check for Python project files
        if self._file_exists("pyproject.toml"):
            python_detected = True
            evidence.append("pyproject.toml found")
            self._detect_python_tools_from_pyproject()

        if self._file_exists("requirements.txt"):
            python_detected = True
            evidence.append("requirements.txt found")

        if self._file_exists("setup.py"):
            python_detected = True
            evidence.append("setup.py found")

        if self._file_exists("Pipfile"):
            python_detected = True
            evidence.append("Pipfile found")
            self._add_technology(
                "Pipenv", TechnologyType.PACKAGE_MANAGER, 0.9, config_file="Pipfile"
            )

        if self._file_exists("poetry.lock"):
            python_detected = True
            evidence.append("poetry.lock found")
            self._add_technology(
                "Poetry", TechnologyType.PACKAGE_MANAGER, 1.0, config_file="poetry.lock"
            )

        # Detect Python version
        if python_detected:
            version = self._detect_python_version()
            self._add_technology(
                "Python",
                TechnologyType.LANGUAGE,
                1.0,
                version=version,
                evidence=evidence,
            )

        # Detect pytest
        if self._file_exists("pytest.ini") or self._file_exists("pyproject.toml"):
            pyproject_content = self._read_file("pyproject.toml")
            if pyproject_content and "[tool.pytest" in pyproject_content:
                self._add_technology(
                    "pytest",
                    TechnologyType.TESTING_FRAMEWORK,
                    0.9,
                    config_file="pyproject.toml",
                )

    def _detect_python_tools_from_pyproject(self):
        """Detect Python tools configured in pyproject.toml."""
        content = self._read_file("pyproject.toml")
        if not content:
            return

        # Detect Ruff
        if "[tool.ruff" in content:
            self._add_technology(
                "Ruff",
                TechnologyType.LINTER,
                1.0,
                config_file="pyproject.toml",
                evidence=["[tool.ruff] section found"],
            )

        # Detect Black
        if "[tool.black" in content:
            self._add_technology(
                "Black",
                TechnologyType.FORMATTER,
                1.0,
                config_file="pyproject.toml",
                evidence=["[tool.black] section found"],
            )

        # Detect mypy
        if "[tool.mypy" in content:
            self._add_technology(
                "mypy",
                TechnologyType.LINTER,
                1.0,
                config_file="pyproject.toml",
                evidence=["[tool.mypy] section found"],
            )

        # Detect isort
        if "[tool.isort" in content:
            self._add_technology(
                "isort",
                TechnologyType.FORMATTER,
                1.0,
                config_file="pyproject.toml",
                evidence=["[tool.isort] section found"],
            )

    def _detect_python_version(self) -> Optional[str]:
        """Detect Python version from pyproject.toml or runtime."""
        # Try pyproject.toml first
        content = self._read_file("pyproject.toml")
        if content:
            # Look for python = "^3.x" pattern
            for line in content.split("\n"):
                if "python" in line and "=" in line:
                    # Extract version like "^3.8", ">=3.8", etc.
                    parts = line.split("=")
                    if len(parts) > 1:
                        version_str = parts[1].strip().strip('"').strip("'")
                        # Remove version specifiers
                        version_str = version_str.lstrip("^>=<~")
                        if version_str and version_str[0].isdigit():
                            return version_str

        # Try python --version command
        output = self._run_command(["python", "--version"])
        if output and "Python" in output:
            return output.split()[-1]

        return None

    # ========================================================================
    # JavaScript/TypeScript Detection
    # ========================================================================

    def detect_javascript(self):
        """Detect JavaScript/TypeScript and related tools."""
        if not self._file_exists("package.json"):
            return

        package_json = self._read_json("package.json")
        if not package_json:
            return

        # Detect Node.js/npm
        self._add_technology(
            "Node.js",
            TechnologyType.LANGUAGE,
            1.0,
            config_file="package.json",
            evidence=["package.json found"],
        )

        self._add_technology(
            "npm",
            TechnologyType.PACKAGE_MANAGER,
            0.9,
            config_file="package.json",
        )

        # Check for yarn/pnpm
        if self._file_exists("yarn.lock"):
            self._add_technology(
                "Yarn",
                TechnologyType.PACKAGE_MANAGER,
                1.0,
                config_file="yarn.lock",
            )

        if self._file_exists("pnpm-lock.yaml"):
            self._add_technology(
                "pnpm",
                TechnologyType.PACKAGE_MANAGER,
                1.0,
                config_file="pnpm-lock.yaml",
            )

        # Detect TypeScript
        if self._file_exists("tsconfig.json"):
            self._add_technology(
                "TypeScript",
                TechnologyType.LANGUAGE,
                1.0,
                config_file="tsconfig.json",
                evidence=["tsconfig.json found"],
            )

        # Detect ESLint
        if self._file_exists(".eslintrc.json") or self._file_exists(".eslintrc.js"):
            config_file = (
                ".eslintrc.json" if self._file_exists(".eslintrc.json") else ".eslintrc.js"
            )
            self._add_technology(
                "ESLint",
                TechnologyType.LINTER,
                1.0,
                config_file=config_file,
            )

        # Detect Prettier
        if self._file_exists(".prettierrc") or self._file_exists("prettier.config.js"):
            config_file = (
                ".prettierrc" if self._file_exists(".prettierrc") else "prettier.config.js"
            )
            self._add_technology(
                "Prettier",
                TechnologyType.FORMATTER,
                1.0,
                config_file=config_file,
            )

        # Detect testing frameworks from package.json
        dev_deps = package_json.get("devDependencies", {})
        dependencies = package_json.get("dependencies", {})
        all_deps = {**dependencies, **dev_deps}

        if "jest" in all_deps:
            self._add_technology(
                "Jest",
                TechnologyType.TESTING_FRAMEWORK,
                0.9,
                version=all_deps["jest"],
                config_file="package.json",
            )

        if "mocha" in all_deps:
            self._add_technology(
                "Mocha",
                TechnologyType.TESTING_FRAMEWORK,
                0.9,
                version=all_deps["mocha"],
                config_file="package.json",
            )

        if "vitest" in all_deps:
            self._add_technology(
                "Vitest",
                TechnologyType.TESTING_FRAMEWORK,
                0.9,
                version=all_deps["vitest"],
                config_file="package.json",
            )

    # ========================================================================
    # Rust Detection
    # ========================================================================

    def detect_rust(self):
        """Detect Rust and related tools."""
        if not self._file_exists("Cargo.toml"):
            return

        self._add_technology(
            "Rust",
            TechnologyType.LANGUAGE,
            1.0,
            config_file="Cargo.toml",
            evidence=["Cargo.toml found"],
        )

        self._add_technology(
            "Cargo",
            TechnologyType.PACKAGE_MANAGER,
            1.0,
            config_file="Cargo.toml",
        )

        # Clippy and rustfmt are standard Rust tools
        self._add_technology(
            "Clippy",
            TechnologyType.LINTER,
            0.8,
            evidence=["Standard Rust linter"],
        )

        self._add_technology(
            "rustfmt",
            TechnologyType.FORMATTER,
            0.8,
            evidence=["Standard Rust formatter"],
        )

    # ========================================================================
    # Go Detection
    # ========================================================================

    def detect_go(self):
        """Detect Go and related tools."""
        if not self._file_exists("go.mod"):
            return

        self._add_technology(
            "Go",
            TechnologyType.LANGUAGE,
            1.0,
            config_file="go.mod",
            evidence=["go.mod found"],
        )

        # Go modules is the package manager
        self._add_technology(
            "Go Modules",
            TechnologyType.PACKAGE_MANAGER,
            1.0,
            config_file="go.mod",
        )

        # Detect golangci-lint config
        if self._file_exists(".golangci.yml") or self._file_exists(".golangci.yaml"):
            config_file = (
                ".golangci.yml" if self._file_exists(".golangci.yml") else ".golangci.yaml"
            )
            self._add_technology(
                "golangci-lint",
                TechnologyType.LINTER,
                1.0,
                config_file=config_file,
            )

        # gofmt is standard
        self._add_technology(
            "gofmt",
            TechnologyType.FORMATTER,
            0.8,
            evidence=["Standard Go formatter"],
        )

    # ========================================================================
    # Ruby Detection
    # ========================================================================

    def detect_ruby(self):
        """Detect Ruby and related tools."""
        if not self._file_exists("Gemfile"):
            return

        self._add_technology(
            "Ruby",
            TechnologyType.LANGUAGE,
            1.0,
            config_file="Gemfile",
            evidence=["Gemfile found"],
        )

        self._add_technology(
            "Bundler",
            TechnologyType.PACKAGE_MANAGER,
            1.0,
            config_file="Gemfile",
        )

        # Detect RuboCop
        if self._file_exists(".rubocop.yml"):
            self._add_technology(
                "RuboCop",
                TechnologyType.LINTER,
                1.0,
                config_file=".rubocop.yml",
            )

    # ========================================================================
    # Java Detection
    # ========================================================================

    def detect_java(self):
        """Detect Java and related tools."""
        maven_detected = self._file_exists("pom.xml")
        gradle_detected = self._file_exists("build.gradle") or self._file_exists("build.gradle.kts")

        if not maven_detected and not gradle_detected:
            return

        self._add_technology(
            "Java",
            TechnologyType.LANGUAGE,
            1.0,
            evidence=["Maven or Gradle config found"],
        )

        if maven_detected:
            self._add_technology(
                "Maven",
                TechnologyType.BUILD_TOOL,
                1.0,
                config_file="pom.xml",
            )

        if gradle_detected:
            config_file = (
                "build.gradle" if self._file_exists("build.gradle") else "build.gradle.kts"
            )
            self._add_technology(
                "Gradle",
                TechnologyType.BUILD_TOOL,
                1.0,
                config_file=config_file,
            )

    # ========================================================================
    # C/C++ Detection
    # ========================================================================

    def detect_cpp(self):
        """Detect C/C++ and related tools."""
        cmake_detected = self._file_exists("CMakeLists.txt")
        makefile_detected = self._file_exists("Makefile")

        if not cmake_detected and not makefile_detected:
            return

        evidence = []
        if cmake_detected:
            evidence.append("CMakeLists.txt found")
        if makefile_detected:
            evidence.append("Makefile found")

        self._add_technology(
            "C/C++",
            TechnologyType.LANGUAGE,
            0.9,
            evidence=evidence,
        )

        if cmake_detected:
            self._add_technology(
                "CMake",
                TechnologyType.BUILD_TOOL,
                1.0,
                config_file="CMakeLists.txt",
            )

        # Detect clang-tidy config
        if self._file_exists(".clang-tidy"):
            self._add_technology(
                "clang-tidy",
                TechnologyType.LINTER,
                1.0,
                config_file=".clang-tidy",
            )

    # ========================================================================
    # Database Detection
    # ========================================================================

    def detect_databases(self):
        """Detect database technologies from config files."""
        # Check docker-compose for database services
        docker_compose_files = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ]

        for compose_file in docker_compose_files:
            content = self._read_file(compose_file)
            if content:
                if "postgres" in content.lower():
                    self._add_technology(
                        "PostgreSQL",
                        TechnologyType.DATABASE,
                        0.8,
                        config_file=compose_file,
                        evidence=["Found in docker-compose"],
                    )
                if "mysql" in content.lower():
                    self._add_technology(
                        "MySQL",
                        TechnologyType.DATABASE,
                        0.8,
                        config_file=compose_file,
                        evidence=["Found in docker-compose"],
                    )
                if "mongo" in content.lower():
                    self._add_technology(
                        "MongoDB",
                        TechnologyType.DATABASE,
                        0.8,
                        config_file=compose_file,
                        evidence=["Found in docker-compose"],
                    )
                if "redis" in content.lower():
                    self._add_technology(
                        "Redis",
                        TechnologyType.DATABASE,
                        0.8,
                        config_file=compose_file,
                        evidence=["Found in docker-compose"],
                    )

    # ========================================================================
    # Container Detection
    # ========================================================================

    def detect_containers(self):
        """Detect containerization technologies."""
        if self._file_exists("Dockerfile"):
            self._add_technology(
                "Docker",
                TechnologyType.CONTAINERIZATION,
                1.0,
                config_file="Dockerfile",
            )

        docker_compose_exists = any(
            self._file_exists(f)
            for f in [
                "docker-compose.yml",
                "docker-compose.yaml",
                "compose.yml",
                "compose.yaml",
            ]
        )

        if docker_compose_exists:
            self._add_technology(
                "Docker Compose",
                TechnologyType.CONTAINERIZATION,
                1.0,
                config_file="docker-compose.yml",
            )

        # Detect Kubernetes
        if self._file_exists("k8s") or self._file_exists("kubernetes"):
            self._add_technology(
                "Kubernetes",
                TechnologyType.CONTAINERIZATION,
                0.9,
                evidence=["k8s/kubernetes directory found"],
            )

    # ========================================================================
    # Main Analysis
    # ========================================================================

    def detect_all(self) -> TechStack:
        """Run all detection methods and return complete tech stack."""
        # Language detection
        self.detect_python()
        self.detect_javascript()
        self.detect_rust()
        self.detect_go()
        self.detect_ruby()
        self.detect_java()
        self.detect_cpp()

        # Infrastructure detection
        self.detect_databases()
        self.detect_containers()

        # Determine primary language
        primary_language = self._determine_primary_language()

        # Calculate overall confidence
        confidence = self._calculate_confidence()

        return TechStack(
            technologies=self.technologies,
            primary_language=primary_language,
            confidence_score=confidence,
            config_files_found=self.config_files,
            warnings=self.warnings,
        )

    def _determine_primary_language(self) -> Optional[str]:
        """Determine primary programming language."""
        languages = [tech for tech in self.technologies if tech.type == TechnologyType.LANGUAGE]

        if not languages:
            return None

        # Return language with highest confidence
        return max(languages, key=lambda x: x.confidence).name

    def _calculate_confidence(self) -> float:
        """Calculate overall detection confidence score."""
        if not self.technologies:
            return 0.0

        # Average confidence of all detections
        total_confidence = sum(tech.confidence for tech in self.technologies)
        return total_confidence / len(self.technologies)


def format_tech_stack_report(stack: TechStack) -> str:
    """Format tech stack analysis as human-readable report."""
    lines = []

    lines.append("# Tech Stack Analysis")
    lines.append("")

    if stack.primary_language:
        lines.append(f"**Primary Language**: {stack.primary_language}")
    lines.append(f"**Confidence Score**: {stack.confidence_score:.0%}")
    lines.append(f"**Configuration Files**: {len(stack.config_files_found)}")
    lines.append("")

    # Group technologies by type
    by_type: Dict[TechnologyType, List[Technology]] = {}
    for tech in stack.technologies:
        if tech.type not in by_type:
            by_type[tech.type] = []
        by_type[tech.type].append(tech)

    # Display by category
    for tech_type in TechnologyType:
        if tech_type not in by_type:
            continue

        techs = by_type[tech_type]
        lines.append(f"## {tech_type.value}")
        for tech in sorted(techs, key=lambda x: x.confidence, reverse=True):
            line = f"- **{tech.name}**"
            if tech.version:
                line += f" (v{tech.version})"
            line += f" - {tech.confidence:.0%} confidence"
            if tech.config_file:
                line += f" - `{tech.config_file}`"
            lines.append(line)

            if tech.evidence:
                for evidence in tech.evidence:
                    lines.append(f"  - {evidence}")

        lines.append("")

    if stack.warnings:
        lines.append("## Warnings")
        for warning in stack.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    if stack.config_files_found:
        lines.append("## Configuration Files Detected")
        for config_file in sorted(stack.config_files_found):
            lines.append(f"- `{config_file}`")
        lines.append("")

    return "\n".join(lines)
