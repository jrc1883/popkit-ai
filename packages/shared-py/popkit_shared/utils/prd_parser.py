#!/usr/bin/env python3
"""
PRD Parser - Product Requirements Document Parsing

Extracts features, user stories, and requirements from markdown PRD documents.
Integrates with complexity analyzer for automatic scoring.

Part of PopKit's Task Master feature set - transforms PRDs into actionable tasks.

Usage:
    from popkit_shared.utils.prd_parser import PRDParser, parse_prd_file

    # Parse a PRD file
    parser = PRDParser()
    result = parser.parse_file("docs/feature-spec.md")

    # Access parsed features
    for feature in result.features:
        print(f"{feature.title}: {feature.complexity_score}/10")
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Feature:
    """Parsed feature from PRD."""

    title: str
    description: str
    level: int  # H1=1, H2=2, etc.
    line_number: int
    acceptance_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity_score: Optional[int] = None
    complexity_analysis: Optional[Dict[str, Any]] = None
    tech_notes: Dict[str, str] = field(default_factory=dict)
    parent_feature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "level": self.level,
            "line_number": self.line_number,
            "complexity_score": self.complexity_score,
            "acceptance_criteria": self.acceptance_criteria,
            "dependencies": self.dependencies,
            "parent_feature": self.parent_feature,
            "has_complexity_analysis": self.complexity_analysis is not None,
        }


@dataclass
class Technology:
    """Identified technology from PRD."""

    name: str
    version: Optional[str] = None
    context: str = ""
    should_research: bool = False
    research_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "context": self.context,
            "should_research": self.should_research,
            "has_research": self.research_notes is not None,
        }


@dataclass
class PRDParseResult:
    """Complete PRD parsing result."""

    document_path: str
    title: str
    features: List[Feature]
    technologies: List[Technology]
    total_features: int
    complexity_distribution: Dict[str, int]  # LOW/MEDIUM/HIGH counts
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_path": self.document_path,
            "title": self.title,
            "total_features": self.total_features,
            "features": [f.to_dict() for f in self.features],
            "technologies": [t.to_dict() for t in self.technologies],
            "complexity_distribution": self.complexity_distribution,
            "metadata": self.metadata,
        }


# =============================================================================
# PRD PARSER
# =============================================================================


class PRDParser:
    """
    Parse markdown PRD documents into structured features with complexity analysis.

    Features:
    - Hierarchical feature parsing (H1-H4)
    - Acceptance criteria extraction
    - Dependency identification
    - Technology detection
    - Automatic complexity analysis integration
    """

    # Technology patterns to detect
    TECH_PATTERNS = [
        # Framework + version
        r"\b([A-Z][a-z]+(?:\.[a-z]+)?)\s+v?(\d+(?:\.\d+)?)",
        # Known frameworks/libraries
        r"\b(React|Vue|Angular|Next\.?js|Nuxt\.?js|Svelte|Remix)\b",
        r"\b(Node\.?js|Express|Fastify|Koa|Hapi)\b",
        r"\b(TypeScript|JavaScript|Python|Go|Rust|Java|C#)\b",
        r"\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch)\b",
        r"\b(Docker|Kubernetes|AWS|Azure|GCP|Vercel|Netlify)\b",
        r"\b(Prisma|Drizzle|TypeORM|Mongoose|Sequelize)\b",
        r"\b(JWT|OAuth|Auth0|Supabase|Firebase)\b",
        r"\b(GraphQL|tRPC|REST|WebSocket|gRPC)\b",
    ]

    # Acceptance criteria indicators
    AC_PATTERNS = [
        r"^[-*]\s+(?:AC|Acceptance|Given|When|Then|Should|Must):",
        r"^[-*]\s+User (?:can|should|must)",
        r"^[-*]\s+System (?:should|must|will)",
    ]

    # Dependency indicators
    DEP_PATTERNS = [
        r"depends on",
        r"requires",
        r"after",
        r"prerequisite",
        r"blocked by",
    ]

    def __init__(self):
        """Initialize PRD parser."""
        self._complexity_analyzer = None

    def _get_complexity_analyzer(self):
        """Get or create complexity analyzer instance."""
        if self._complexity_analyzer is None:
            try:
                # Try relative import first (when used as package)
                from .complexity_scoring import get_complexity_analyzer

                self._complexity_analyzer = get_complexity_analyzer()
            except ImportError:
                try:
                    # Fall back to absolute import (when run as script)
                    from popkit_shared.utils.complexity_scoring import get_complexity_analyzer

                    self._complexity_analyzer = get_complexity_analyzer()
                except ImportError:
                    try:
                        # Last resort: direct import from same directory
                        import complexity_scoring

                        self._complexity_analyzer = complexity_scoring.get_complexity_analyzer()
                    except ImportError:
                        pass
        return self._complexity_analyzer

    # =========================================================================
    # MAIN PARSING
    # =========================================================================

    def parse_file(self, file_path: str) -> PRDParseResult:
        """
        Parse PRD file and return structured result.

        Args:
            file_path: Path to markdown PRD file

        Returns:
            PRDParseResult with parsed features and analysis
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PRD file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.parse_content(content, str(path))

    def parse_content(self, content: str, source_path: str = "inline") -> PRDParseResult:
        """
        Parse PRD content and return structured result.

        Args:
            content: Markdown content to parse
            source_path: Source identifier for the content

        Returns:
            PRDParseResult with parsed features and analysis
        """
        # Extract document title
        title = self._extract_title(content)

        # Parse features hierarchically
        features = self._parse_features(content)

        # Extract technologies
        technologies = self._extract_technologies(content)

        # Analyze complexity for each feature
        self._analyze_feature_complexity(features)

        # Build complexity distribution
        complexity_dist = self._calculate_complexity_distribution(features)

        # Extract metadata
        metadata = {
            "line_count": len(content.split("\n")),
            "has_acceptance_criteria": any(f.acceptance_criteria for f in features),
            "has_dependencies": any(f.dependencies for f in features),
            "avg_complexity": self._calculate_avg_complexity(features),
        }

        return PRDParseResult(
            document_path=source_path,
            title=title,
            features=features,
            technologies=technologies,
            total_features=len(features),
            complexity_distribution=complexity_dist,
            metadata=metadata,
        )

    # =========================================================================
    # FEATURE PARSING
    # =========================================================================

    def _extract_title(self, content: str) -> str:
        """Extract document title (first H1)."""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else "Untitled PRD"

    def _parse_features(self, content: str) -> List[Feature]:
        """Parse features hierarchically from markdown headers."""
        features = []
        lines = content.split("\n")

        current_feature = None
        parent_stack: List[tuple] = []  # (level, title)

        for i, line in enumerate(lines, 1):
            # Check for header (H1-H4)
            header_match = re.match(r"^(#{1,4})\s+(.+)$", line)

            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()

                # Skip H1 (document title)
                if level == 1:
                    continue

                # Save previous feature
                if current_feature:
                    features.append(current_feature)

                # Update parent stack
                while parent_stack and parent_stack[-1][0] >= level:
                    parent_stack.pop()

                parent_title = parent_stack[-1][1] if parent_stack else None

                # Create new feature
                current_feature = Feature(
                    title=title,
                    description="",
                    level=level,
                    line_number=i,
                    parent_feature=parent_title,
                )

                # Add to parent stack
                parent_stack.append((level, title))

            elif current_feature:
                # Accumulate description
                stripped = line.strip()

                if stripped:
                    # Check for acceptance criteria
                    if any(
                        re.match(pattern, stripped, re.IGNORECASE) for pattern in self.AC_PATTERNS
                    ):
                        current_feature.acceptance_criteria.append(stripped)

                    # Check for dependencies
                    elif any(keyword in stripped.lower() for keyword in self.DEP_PATTERNS):
                        current_feature.dependencies.append(stripped)

                    # Add to description
                    else:
                        current_feature.description += line + "\n"

        # Save last feature
        if current_feature:
            features.append(current_feature)

        return features

    # =========================================================================
    # TECHNOLOGY EXTRACTION
    # =========================================================================

    def _extract_technologies(self, content: str) -> List[Technology]:
        """Extract technology mentions from content."""
        technologies: Dict[str, Technology] = {}

        for pattern in self.TECH_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)

            for match in matches:
                tech_name = match.group(1)
                tech_version = match.group(2) if match.lastindex >= 2 else None

                # Get context (surrounding text)
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].replace("\n", " ")

                # Create or update technology entry
                tech_key = tech_name.lower()
                if tech_key not in technologies:
                    technologies[tech_key] = Technology(
                        name=tech_name,
                        version=tech_version,
                        context=context,
                        should_research=self._should_research_tech(tech_name, tech_version),
                    )

        return list(technologies.values())

    def _should_research_tech(self, name: str, version: Optional[str]) -> bool:
        """Determine if technology should be researched."""
        # Research if version is specified (likely recent)
        if version:
            try:
                major = int(version.split(".")[0])
                # Research if version is recent (subjective threshold)
                if major >= 15:  # e.g., Next.js 15, React 19
                    return True
            except (ValueError, IndexError):
                pass

        # Research newer frameworks
        recent_frameworks = {
            "remix",
            "astro",
            "qwik",
            "solid",
            "fresh",
            "bun",
            "deno",
            "elysia",
            "hono",
            "drizzle",
            "trpc",
            "tanstack",
        }

        return name.lower() in recent_frameworks

    # =========================================================================
    # COMPLEXITY ANALYSIS
    # =========================================================================

    def _analyze_feature_complexity(self, features: List[Feature]) -> None:
        """Analyze complexity for each feature using complexity_scoring module."""
        analyzer = self._get_complexity_analyzer()

        if not analyzer:
            # No complexity analyzer available
            return

        for feature in features:
            try:
                # Build analysis context
                metadata = {
                    "acceptance_criteria": len(feature.acceptance_criteria),
                    "dependencies": len(feature.dependencies),
                    "level": feature.level,
                }

                # Analyze complexity
                analysis = analyzer.analyze(
                    f"{feature.title}\n\n{feature.description}", metadata=metadata
                )

                # Store results
                feature.complexity_score = analysis.complexity_score
                feature.complexity_analysis = analysis.to_dict()

            except Exception:
                # Silently skip on error
                pass

    def _calculate_complexity_distribution(self, features: List[Feature]) -> Dict[str, int]:
        """Calculate complexity distribution across features."""
        distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "UNKNOWN": 0}

        for feature in features:
            if feature.complexity_score is None:
                distribution["UNKNOWN"] += 1
            elif feature.complexity_score <= 3:
                distribution["LOW"] += 1
            elif feature.complexity_score <= 6:
                distribution["MEDIUM"] += 1
            else:
                distribution["HIGH"] += 1

        return distribution

    def _calculate_avg_complexity(self, features: List[Feature]) -> Optional[float]:
        """Calculate average complexity score."""
        scores = [f.complexity_score for f in features if f.complexity_score is not None]

        if not scores:
            return None

        return sum(scores) / len(scores)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def parse_prd_file(file_path: str) -> PRDParseResult:
    """
    Parse PRD file (convenience function).

    Args:
        file_path: Path to markdown PRD file

    Returns:
        PRDParseResult with parsed features and analysis
    """
    parser = PRDParser()
    return parser.parse_file(file_path)


def parse_prd_content(content: str) -> PRDParseResult:
    """
    Parse PRD content (convenience function).

    Args:
        content: Markdown content to parse

    Returns:
        PRDParseResult with parsed features and analysis
    """
    parser = PRDParser()
    return parser.parse_content(content)


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    import sys

    print("PRD Parser Test\n" + "=" * 50)

    # Test with sample PRD
    sample_prd = """# User Authentication System

Build a secure authentication system with JWT tokens and refresh token rotation.

## Features

### Login Flow
User authentication with email/password and OAuth providers.

- AC: User can login with email and password
- AC: User can login with Google OAuth
- AC: System must implement brute force protection
- Requires: Email verification system

Implementation notes:
- Use Next.js 15 App Router for pages
- JWT tokens with 15-minute expiration
- Redis for session management

### Registration
New user registration with email verification.

- AC: User can create account with email/password
- AC: System sends verification email
- AC: Password must meet strength requirements
- Depends on: Email service integration

### Security Features
Security hardening and token management.

- AC: JWT refresh token rotation implemented
- AC: Secure cookie storage with httpOnly flag
- AC: CSRF protection enabled

Technologies:
- Prisma ORM for user storage
- WebSockets for real-time logout
"""

    print("Parsing sample PRD...\n")
    parser = PRDParser()
    result = parser.parse_content(sample_prd)

    print(f"Document: {result.title}")
    print(f"Features: {result.total_features}")
    print("\nComplexity Distribution:")
    for level, count in result.complexity_distribution.items():
        print(f"  {level}: {count}")

    print("\nTechnologies Identified:")
    for tech in result.technologies:
        research = " (should research)" if tech.should_research else ""
        version = f" v{tech.version}" if tech.version else ""
        print(f"  - {tech.name}{version}{research}")

    print("\nFeatures:")
    for feature in result.features:
        indent = "  " * (feature.level - 2)
        complexity = f" [{feature.complexity_score}/10]" if feature.complexity_score else ""
        print(f"{indent}- {feature.title}{complexity}")
        if feature.acceptance_criteria:
            print(f"{indent}  AC: {len(feature.acceptance_criteria)}")
        if feature.dependencies:
            print(f"{indent}  Deps: {len(feature.dependencies)}")

    # Test file parsing if path provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"\n\nParsing file: {file_path}")
        print("=" * 50)

        try:
            result = parse_prd_file(file_path)

            print(f"Document: {result.title}")
            print(f"Features: {result.total_features}")
            avg_complexity = result.metadata.get("avg_complexity")
            if avg_complexity is not None:
                print(f"Avg Complexity: {avg_complexity:.1f}/10")
            else:
                print("Avg Complexity: N/A")

            print("\nHigh Complexity Features:")
            high_complexity = [
                f for f in result.features if f.complexity_score and f.complexity_score >= 7
            ]
            for feature in high_complexity:
                print(f"  - {feature.title} [{feature.complexity_score}/10]")

        except Exception as e:
            print(f"Error: {e}")

    print("\n[OK] All tests completed!")
