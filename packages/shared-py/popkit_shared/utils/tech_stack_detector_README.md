# Tech Stack Detector

**Phase 1 Implementation for Issue #155**

Intelligent technology stack detection for PopKit projects. Automatically identifies programming languages, package managers, linters, formatters, testing frameworks, databases, and containerization technologies.

## Features

### Supported Technologies

| Category               | Technologies                                                                    |
| ---------------------- | ------------------------------------------------------------------------------- |
| **Languages**          | Python, JavaScript/TypeScript, Rust, Go, Ruby, Java, C/C++                      |
| **Package Managers**   | pip, Poetry, Pipenv, npm, Yarn, pnpm, Cargo, Go Modules, Bundler, Maven, Gradle |
| **Linters**            | Ruff, mypy, ESLint, Clippy, golangci-lint, RuboCop, clang-tidy                  |
| **Formatters**         | Black, isort, Prettier, rustfmt, gofmt                                          |
| **Testing Frameworks** | pytest, Jest, Mocha, Vitest                                                     |
| **Databases**          | PostgreSQL, MySQL, MongoDB, Redis                                               |
| **Containerization**   | Docker, Docker Compose, Kubernetes                                              |
| **Build Tools**        | CMake, Maven, Gradle                                                            |

### Detection Patterns

Technologies are detected via:

- **Configuration files**: `pyproject.toml`, `package.json`, `Cargo.toml`, etc.
- **Lock files**: `poetry.lock`, `yarn.lock`, `Cargo.lock`, etc.
- **Docker files**: `Dockerfile`, `docker-compose.yml`, `k8s/` directory
- **Tool-specific configs**: `.eslintrc.json`, `.rubocop.yml`, etc.

### Confidence Scoring

Each detected technology includes a confidence score (0.0-1.0):

- **1.0**: Explicit configuration file found (e.g., `tsconfig.json` → TypeScript)
- **0.9**: Inferred from package manager (e.g., `package.json` → Node.js)
- **0.8**: Standard tool inferred from language (e.g., Rust → Clippy)

## Usage

### Basic Usage

```python
from popkit_shared.utils.tech_stack_detector import TechStackDetector

# Detect technologies in current directory
detector = TechStackDetector(".")
stack = detector.detect_all()

print(f"Primary Language: {stack.primary_language}")
print(f"Confidence: {stack.confidence_score:.0%}")
print(f"Technologies: {len(stack.technologies)}")

for tech in stack.technologies:
    print(f"  - {tech.name} ({tech.type.value}): {tech.confidence:.0%}")
```

### Generate Report

```python
from popkit_shared.utils.tech_stack_detector import (
    TechStackDetector,
    format_tech_stack_report,
)

detector = TechStackDetector(".")
stack = detector.detect_all()
report = format_tech_stack_report(stack)

print(report)
```

**Example Output:**

```markdown
# Tech Stack Analysis

**Primary Language**: Python
**Confidence Score**: 95%
**Configuration Files**: 5

## Language

- **Python** (v3.11) - 100% confidence - `pyproject.toml`
  - pyproject.toml found
  - requirements.txt found

## Linter

- **Ruff** - 100% confidence - `pyproject.toml`
  - [tool.ruff] section found
- **mypy** - 100% confidence - `pyproject.toml`
  - [tool.mypy] section found

## Formatter

- **Black** - 100% confidence - `pyproject.toml`
  - [tool.black] section found

## Package Manager

- **Poetry** - 100% confidence - `poetry.lock`

## Testing Framework

- **pytest** - 90% confidence - `pyproject.toml`

## Containerization

- **Docker** - 100% confidence - `Dockerfile`
- **Docker Compose** - 100% confidence - `docker-compose.yml`

## Configuration Files Detected

- `pyproject.toml`
- `requirements.txt`
- `poetry.lock`
- `Dockerfile`
- `docker-compose.yml`
```

### Advanced Usage

#### Detect Specific Language

```python
detector = TechStackDetector(".")

# Only detect Python tools
detector.detect_python()

# Only detect JavaScript/TypeScript tools
detector.detect_javascript()

# Access detected technologies
for tech in detector.technologies:
    print(f"{tech.name}: {tech.version or 'N/A'}")
```

#### Filter by Technology Type

```python
from popkit_shared.utils.tech_stack_detector import TechnologyType

detector = TechStackDetector(".")
stack = detector.detect_all()

# Get all linters
linters = [
    tech for tech in stack.technologies
    if tech.type == TechnologyType.LINTER
]

# Get all languages
languages = [
    tech for tech in stack.technologies
    if tech.type == TechnologyType.LANGUAGE
]
```

#### Handle Multi-Language Projects

```python
detector = TechStackDetector(".")
stack = detector.detect_all()

# Primary language is determined by highest confidence
print(f"Primary: {stack.primary_language}")

# All detected languages
languages = [
    tech for tech in stack.technologies
    if tech.type == TechnologyType.LANGUAGE
]

for lang in languages:
    print(f"  - {lang.name}: {lang.confidence:.0%}")
```

## Data Structures

### Technology

Represents a single detected technology:

```python
@dataclass
class Technology:
    name: str                    # Technology name (e.g., "Ruff", "TypeScript")
    type: TechnologyType         # Category (LANGUAGE, LINTER, etc.)
    confidence: float            # Detection confidence (0.0-1.0)
    version: Optional[str]       # Version if detected
    config_file: Optional[str]   # Config file path if found
    evidence: List[str]          # Evidence for detection
```

### TechStack

Complete analysis results:

```python
@dataclass
class TechStack:
    technologies: List[Technology]     # All detected technologies
    primary_language: Optional[str]    # Main language (highest confidence)
    confidence_score: float            # Overall confidence (average)
    config_files_found: List[str]      # All config files detected
    warnings: List[str]                # Any issues during detection
```

### TechnologyType

Technology categories:

```python
class TechnologyType(Enum):
    LANGUAGE = "Language"
    PACKAGE_MANAGER = "Package Manager"
    TESTING_FRAMEWORK = "Testing Framework"
    LINTER = "Linter"
    FORMATTER = "Formatter"
    DATABASE = "Database"
    CONTAINERIZATION = "Containerization"
    BUILD_TOOL = "Build Tool"
    OTHER = "Other"
```

## Integration with PopKit

### Use in Commands

```python
# In a PopKit command
from popkit_shared.utils.tech_stack_detector import TechStackDetector

def analyze_project_command():
    detector = TechStackDetector(project_path)
    stack = detector.detect_all()

    # Include in analysis report
    print(f"## Tech Stack")
    print(f"Primary Language: {stack.primary_language}")

    # Use for recommendations
    if stack.primary_language == "Python":
        recommend_python_checks(stack)
    elif stack.primary_language == "Node.js":
        recommend_js_checks(stack)
```

### Use in Skills

```python
# In a PopKit skill
from popkit_shared.utils.tech_stack_detector import TechStackDetector, TechnologyType

def recommend_quality_checks():
    detector = TechStackDetector(".")
    stack = detector.detect_all()

    # Check for missing linters
    has_linter = any(
        tech.type == TechnologyType.LINTER
        for tech in stack.technologies
    )

    if not has_linter and stack.primary_language:
        print(f"⚠️ No linter detected for {stack.primary_language}")
        recommend_linter(stack.primary_language)
```

## Testing

Comprehensive test suite with 48 tests covering:

- Python detection (8 tests)
- JavaScript/TypeScript detection (7 tests)
- Rust detection (4 tests)
- Go detection (4 tests)
- Ruby detection (3 tests)
- Java detection (3 tests)
- C/C++ detection (3 tests)
- Database detection (4 tests)
- Container detection (3 tests)
- Multi-language projects (2 tests)
- Analysis and reporting (7 tests)

Run tests:

```bash
cd packages/shared-py
pytest popkit_shared/tests/test_tech_stack_detector.py -v
```

## Future Enhancements (Phase 2+)

This is Phase 1 implementation. Future phases will add:

- **Phase 2**: Recommendation engine for missing tools
- **Phase 3**: Automatic setup of pre-commit hooks and CI
- **Integration**: Add to `/popkit-core:project analyze`
- **Caching**: Session-level caching for performance
- **Extensibility**: User-defined detection rules

See [Issue #155](https://github.com/jrc1883/popkit-ai/issues/155) for full roadmap.

## Design Patterns

This module follows PopKit's established patterns:

- **Dataclasses**: For structured data (`Technology`, `TechStack`)
- **Enums**: For type safety (`TechnologyType`)
- **Confidence scoring**: Similar to `git_strategy.py`
- **File-based detection**: Explicit config files prioritized
- **Comprehensive testing**: 90%+ coverage target
- **Ruff compliance**: Clean linting and formatting

## Examples

### Example 1: Python Project

**Project Structure:**

```
project/
├── pyproject.toml  ([tool.ruff], [tool.mypy])
├── requirements.txt
└── tests/
```

**Detection:**

```python
detector = TechStackDetector("project")
stack = detector.detect_all()

# Results:
# - Python (1.0 confidence)
# - Ruff (1.0 confidence)
# - mypy (1.0 confidence)
# - pytest (0.9 confidence if [tool.pytest] exists)
```

### Example 2: Full-Stack Project

**Project Structure:**

```
project/
├── backend/
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   └── .eslintrc.json
├── Dockerfile
└── docker-compose.yml
```

**Detection:**

```python
detector = TechStackDetector("project")
stack = detector.detect_all()

# Results:
# Languages: Python, Node.js, TypeScript
# Linters: Ruff, ESLint
# Containers: Docker, Docker Compose
# Primary Language: Python (highest confidence from pyproject.toml)
```

### Example 3: Monorepo

**Project Structure:**

```
monorepo/
├── services/
│   ├── api/ (Python)
│   └── worker/ (Go)
├── web/ (TypeScript)
└── mobile/ (Rust)
```

**Detection:**

```python
detector = TechStackDetector("monorepo")
stack = detector.detect_all()

# Results:
# Languages: Python, Go, TypeScript, Rust
# Primary: Determined by most explicit config
# All associated tools detected per language
```

## Troubleshooting

### No Technologies Detected

**Issue**: `stack.technologies` is empty

**Solutions**:

1. Ensure project has config files (`pyproject.toml`, `package.json`, etc.)
2. Check path is correct: `TechStackDetector("/absolute/path/to/project")`
3. Verify file permissions (must be readable)

### Low Confidence Scores

**Issue**: All detections have low confidence

**Explanation**:

- Confidence < 0.9 means inferred rather than explicit
- Add explicit config files for higher confidence
- Example: Add `tsconfig.json` for TypeScript (1.0 vs 0.9)

### Version Not Detected

**Issue**: `tech.version` is None

**Explanation**:

- Version detection is optional and best-effort
- Only available for some tools (e.g., package.json dependencies)
- Not critical for tech stack identification

## Contributing

When adding new technology detection:

1. Add detection method (e.g., `detect_kotlin()`)
2. Add to `detect_all()` method
3. Write comprehensive tests (minimum 3 tests per technology)
4. Update this README with supported technologies
5. Run Ruff: `ruff check --fix` and `ruff format`
6. Verify tests: `pytest popkit_shared/tests/test_tech_stack_detector.py`

## License

MIT

---

**Issue**: [#155 - Tech Stack Detection & Automated Check Recommendations](https://github.com/jrc1883/popkit-ai/issues/155)
**Phase**: 1 of 3 (Detection Engine)
**Status**: ✅ Complete
