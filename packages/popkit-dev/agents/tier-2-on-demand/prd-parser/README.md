# PRD Parser Agent

**High Priority Quick Win** - Demonstrates seamless PopKit feature integration

## Overview

The PRD Parser agent transforms Product Requirements Documents (PRDs) into structured, actionable implementation plans with automatic complexity analysis and technology research.

## Key Features

- **PRD Parsing**: Extracts features, user stories, acceptance criteria from markdown
- **Automatic Complexity Analysis**: Uses `complexity_scoring.py` to score each feature (1-10 scale)
- **Technology Research**: Auto-researches unfamiliar technologies via WebSearch
- **Task Generation**: Creates TodoWrite lists with proper breakdown
- **GitHub Integration**: Optionally creates issues for high-priority features
- **Implementation Roadmap**: Generates phased execution plan with estimates

## Integration Showcase

This agent demonstrates **seamless integration** between PopKit features:

1. **Complexity Analyzer** (`complexity_scoring.py`)
   - Automatic invocation during PRD parsing
   - Scores every feature (1-10 scale)
   - Provides subtask recommendations
   - Identifies risk factors
   - Generates phase distribution

2. **WebSearch** (Technology Research)
   - Auto-detects mentioned technologies
   - Researches new versions (Next.js 15, React 19)
   - Researches unfamiliar frameworks (Remix, Astro, Qwik)
   - Provides best practices and recent changes
   - Skips well-known, stable technologies

3. **TodoWrite** (Task Management)
   - Auto-generates task list from features
   - Includes complexity scores and metadata
   - Ready for `/popkit:dev` workflows
   - Proper priority ordering

4. **GitHub Issues** (Project Tracking)
   - Bulk issue creation with user confirmation
   - Rich issue bodies with complexity analysis
   - Proper labeling (feature, complexity level)
   - Acceptance criteria included

## Usage

### Parse a PRD

```
User: "Parse this PRD: docs/feature-spec.md"
```

The agent will:
1. Read and parse the PRD file
2. Extract all features (H2-H4 headers)
3. Analyze complexity automatically (via complexity_scoring.py)
4. Research mentioned technologies (via WebSearch)
5. Generate TodoWrite list with all features
6. Ask about creating GitHub issues
7. Create detailed breakdown document
8. Output structured implementation plan

### Example Output

```
📋 PRD PARSER COMPLETE

Document: User Authentication System
Features: 12 identified (4 LOW, 6 MEDIUM, 2 HIGH)

Complexity Analysis:
- Average: 5.8/10
- HIGH (7-10): 2 features requiring careful planning
- MEDIUM (4-6): 6 features for foundation building
- LOW (1-3): 4 features as quick wins

Technologies Researched:
✓ Next.js 15 (via WebSearch) - Server Actions, PPR, Turbopack
✓ Prisma ORM (existing knowledge)
✓ Redis (existing knowledge)

Generated Artifacts:
✓ TodoWrite: 12 tasks created
✓ Breakdown: .workspace/prd-breakdown-user-auth-system.md
✓ GitHub Issues: 2 HIGH priority issues (#42, #43)

Estimated Timeline: 28 days (4 weeks)

Next: /popkit:dev work 1
```

## Technical Implementation

### PRD Parser Utility

Located at: `packages/shared-py/popkit_shared/utils/prd_parser.py`

```python
from popkit_shared.utils.prd_parser import parse_prd_file

# Parse a PRD file
result = parse_prd_file("docs/feature-spec.md")

# Access parsed features
for feature in result.features:
    print(f"{feature.title}: {feature.complexity_score}/10")
    print(f"  Subtasks: {len(feature.acceptance_criteria)}")
    print(f"  Risks: {feature.complexity_analysis['risk_factors']}")

# Access technologies
for tech in result.technologies:
    if tech.should_research:
        print(f"Research: {tech.name} {tech.version}")
```

### Complexity Integration

The PRD parser automatically invokes the complexity analyzer:

```python
# Happens automatically in parse_prd_file()
from popkit_shared.utils.complexity_scoring import get_complexity_analyzer

analyzer = get_complexity_analyzer()

for feature in features:
    analysis = analyzer.analyze(
        feature.description,
        metadata={
            "acceptance_criteria": feature.acceptance_criteria,
            "dependencies": feature.dependencies
        }
    )

    feature.complexity_score = analysis.complexity_score
    feature.complexity_analysis = analysis.to_dict()
```

### Research Integration

Technologies are researched via WebSearch when needed:

```python
# Auto-research unfamiliar technologies
for tech in result.technologies:
    if tech.should_research:
        # Use WebSearch tool
        research = WebSearch(
            query=f"{tech.name} {tech.version} overview best practices 2026"
        )

        # Extract key insights
        tech.research_notes = extract_key_points(research)
```

**Research triggers:**
- New versions: Next.js 15, React 19, Vue 4
- Recent frameworks: Remix, Astro, Qwik, Solid
- Modern tools: Bun, Deno, Elysia, Hono
- New ORMs: Drizzle, Kysely

**Skip research:**
- Established frameworks: React 18 and below
- Common tools: Express, PostgreSQL, Redis
- Well-known libraries with stable APIs

## PRD Format

The parser expects markdown PRDs with this structure:

```markdown
# Document Title

Brief overview...

## Features

### Feature Name (H3)

Feature description and requirements.

**Acceptance Criteria:**
- AC: User can do X
- AC: System must do Y

**Dependencies:**
- Requires: Feature Z
- Depends on: Service A

**Technical Requirements:**
- Use Technology X
- Implement pattern Y
```

**Key patterns:**
- H1: Document title (skipped as feature)
- H2: Major sections (Features, Technical Stack, etc.)
- H3-H4: Individual features and sub-features
- Bullets starting with "AC:" extracted as acceptance criteria
- Mentions of "depends", "requires", "after" extracted as dependencies
- Technology names with versions detected automatically

## Testing

Test the PRD parser utility:

```bash
# Test with built-in sample
cd packages/shared-py
python popkit_shared/utils/prd_parser.py

# Test with actual PRD file
python popkit_shared/utils/prd_parser.py path/to/your-prd.md
```

Test the agent:

```
# Parse the test PRD
User: "Parse .workspace/test-prd-user-auth.md"

# Expected output:
# - 6 features extracted (Login, Registration, Password, OAuth, Session, Security)
# - Complexity scores for each
# - Technologies: Next.js 15, Prisma, Redis, OAuth
# - TodoWrite list created
# - Breakdown document generated
```

## Value Proposition

**Time Savings:**
- Manual PRD breakdown: 2-4 hours
- Automated parsing: 2-5 minutes
- **95%+ time reduction**

**Quality Improvements:**
- Consistent task breakdown across PRDs
- No missed acceptance criteria
- Complexity-informed estimates from the start
- Technology research upfront (no surprises)
- Risk factors identified early

**Integration Benefits:**
- Seamless handoff to `/popkit:dev` workflows
- Complexity already analyzed (no re-analysis needed)
- Technologies already researched
- TodoWrite already populated
- GitHub issues ready for tracking

## Example: Real PRD Parsing

Given this PRD:

```markdown
# E-commerce Checkout Flow

## Features

### Shopping Cart
Persistent cart with quantity management.

- AC: User can add items to cart
- AC: User can update quantities
- AC: Cart persists across sessions
- Requires: Product catalog system

### Payment Processing
Secure payment with Stripe integration.

- AC: User can enter payment details
- AC: System processes payment securely
- AC: User receives order confirmation
- Depends on: Shopping cart completion
```

The parser produces:

```
Features: 2
- Shopping Cart [4/10]
  - Subtasks: 2-4 recommended
  - AC: 3 criteria
  - Deps: 1 (Product catalog)
  - Risks: None

- Payment Processing [7/10]
  - Subtasks: 5-7 recommended
  - AC: 3 criteria
  - Deps: 1 (Shopping cart)
  - Risks: security_critical, integration_complexity

TodoWrite: 2 tasks created
Estimated: 7-11 days total
```

## Roadmap

**Current (v1.0.0):**
- ✓ Markdown PRD parsing
- ✓ Complexity analysis integration
- ✓ Technology detection and research
- ✓ TodoWrite generation
- ✓ GitHub issue creation

**Future enhancements:**
- Support for YAML frontmatter in PRDs
- Extract user personas and journeys
- Generate API specifications from PRDs
- Create test plans from acceptance criteria
- Export to Jira/Linear/Asana formats
- PRD version comparison and diff
- Multi-document PRD aggregation

## Related Components

- **Complexity Analyzer** (`complexity_scoring.py`) - Feature scoring
- **GitHub Issues Utility** (`github_issues.py`) - Issue creation
- **WebSearch** - Technology research
- **TodoWrite** - Task management integration

## Files

```
packages/popkit-dev/agents/tier-2-on-demand/prd-parser/
├── AGENT.md           # Agent definition and instructions
├── README.md          # This file
└── .../               # Future additions

packages/shared-py/popkit_shared/utils/
├── prd_parser.py      # Core parsing utility
├── complexity_scoring.py  # Complexity analysis
└── github_issues.py   # GitHub integration

.workspace/
└── test-prd-user-auth.md  # Example PRD for testing
```

## Contributing

To improve the PRD parser:

1. **Add more technology patterns** in `prd_parser.py`
2. **Improve acceptance criteria detection** (more patterns)
3. **Enhance dependency extraction** (better heuristics)
4. **Add support for additional PRD formats**

## License

MIT - Part of PopKit plugin suite
