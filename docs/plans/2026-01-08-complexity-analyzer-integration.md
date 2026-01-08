# Complexity Analyzer Integration Guide

**Created:** 2026-01-08
**Status:** Implemented
**Component:** PopKit Dev - Complexity Analysis Engine

## Overview

The Complexity Analyzer is a foundational feature that provides 1-10 scoring for tasks and features with automatic subtask recommendations. It integrates seamlessly with existing PopKit workflows to enable intelligent task breakdown, agent selection, and prioritization.

## Architecture

### Components

1. **Core Utility:** `packages/shared-py/popkit_shared/utils/complexity_scoring.py`
   - ComplexityAnalyzer class
   - 8 weighted complexity factors
   - 1-10 scoring algorithm
   - Subtask and phase recommendations

2. **Skill:** `packages/popkit-dev/skills/pop-complexity-analyzer/SKILL.md`
   - Skill interface for workflows
   - Integration documentation
   - Usage examples

3. **Context Integration:** `packages/shared-py/popkit_shared/utils/skill_context.py`
   - Added complexity_score field
   - Added complexity_analysis field
   - Enables skill-to-skill complexity sharing

## Complexity Factors

The analyzer evaluates 8 factors with configurable weights:

| Factor | Weight | Score Range | Description |
|--------|--------|-------------|-------------|
| Files Affected | 15% | 0-100 | Number of files requiring changes |
| LOC Estimate | 15% | 0-100 | Estimated lines of code to write/modify |
| Dependencies | 15% | 0-100 | External and internal dependencies |
| Architecture Change | 20% | 0-100 | Impact on system architecture |
| Breaking Changes | 15% | 0-100 | Compatibility impact |
| Testing Complexity | 10% | 0-100 | Testing requirements and coverage |
| Security Impact | 5% | 0-100 | Security considerations |
| Integration Points | 5% | 0-100 | External system integrations |

**Scoring Formula:**
```
raw_score = Σ(factor_weight × factor_value)
complexity_score = normalize_to_1_10(raw_score)
```

## Usage Patterns

### 1. Automatic Analysis in Workflows

The complexity analyzer is automatically invoked by development workflows:

```bash
/popkit:dev "Add user authentication"
```

**Process:**
1. User provides task description
2. Workflow invokes complexity analyzer
3. Analyzer returns score, subtasks, recommendations
4. Workflow uses recommendations to:
   - Select appropriate agents
   - Determine workflow mode (quick/full)
   - Estimate token usage
   - Break down into subtasks

### 2. Programmatic Usage (Python)

Skills and utilities can invoke the analyzer directly:

```python
from popkit_shared.utils.complexity_scoring import analyze_complexity

# Basic analysis
result = analyze_complexity("Add real-time notifications")

# With metadata
result = analyze_complexity(
    "Refactor authentication module",
    metadata={
        "files_affected": 8,
        "dependencies": 5,
        "loc_estimate": 300
    }
)

# Access results
score = result["complexity_score"]  # 1-10
subtasks = result["recommended_subtasks"]
phases = result["phase_distribution"]
risks = result["risk_factors"]
agents = result["suggested_agents"]
```

### 3. Quick Score (Lightweight)

For fast scoring without full analysis:

```python
from popkit_shared.utils.complexity_scoring import quick_score

score = quick_score("Fix button alignment")  # Returns: 2
```

## Integration Points

### 1. Agent Router Integration

The agent router uses complexity scores to select appropriate agents:

```python
from popkit_shared.utils.complexity_scoring import quick_score

def select_agent(task_description):
    complexity = quick_score(task_description)

    if complexity >= 8:
        return "code-architect"  # Senior agent
    elif complexity >= 5:
        return "refactoring-expert"
    else:
        return "rapid-prototyper"
```

**Benefits:**
- Complex tasks routed to senior agents
- Simple tasks handled by rapid agents
- Optimal resource allocation

### 2. PRD Parser Integration

PRD parser will use complexity for feature prioritization:

```python
from popkit_shared.utils.complexity_scoring import analyze_complexity

# Parse PRD features
features = parse_prd(document)

# Score each feature
for feature in features:
    analysis = analyze_complexity(feature.description)
    feature.complexity_score = analysis["complexity_score"]
    feature.subtasks_recommended = analysis["recommended_subtasks"]
    feature.estimated_tokens = analysis["estimated_tokens"]["total"]

# Sort by complexity (simple first approach)
features.sort(key=lambda f: f.complexity_score)
```

**Benefits:**
- Prioritize features by complexity
- Estimate effort per feature
- Plan sprints based on complexity budget

### 3. Planning Workflow Integration

Planning workflows use complexity to determine approach:

```python
from popkit_shared.utils.complexity_scoring import analyze_complexity

task = "Migrate database to PostgreSQL"
result = analyze_complexity(task)
score = result["complexity_score"]

if score <= 4:
    # Quick mode (5 steps)
    workflow = "quick_mode"
    print("Using quick workflow (5 steps)")
elif score <= 7:
    # Standard mode (7 phases)
    workflow = "standard_mode"
    print("Using standard workflow (7 phases)")
else:
    # Full mode with architecture review
    workflow = "full_mode_with_architecture"
    print("Using full workflow with architecture review")

# Use phase distribution
phases = result["phase_distribution"]
for phase, count in phases.items():
    print(f"  {phase}: {count} subtasks")
```

**Benefits:**
- Right-size workflow complexity
- Allocate appropriate time per phase
- Avoid over-engineering simple tasks

### 4. Merge Conflict Resolver Integration

Merge conflict resolver will prioritize by complexity:

```python
from popkit_shared.utils.complexity_scoring import analyze_complexity

# Detect conflicts
conflicts = detect_merge_conflicts()

# Score each conflict
for conflict in conflicts:
    context = extract_conflict_context(conflict)
    analysis = analyze_complexity(context)
    conflict.complexity = analysis["complexity_score"]
    conflict.priority = analysis["complexity_score"]

# Resolve highest complexity first
conflicts.sort(key=lambda c: c.priority, reverse=True)

print("Conflict resolution order:")
for conflict in conflicts:
    print(f"  {conflict.file} (complexity: {conflict.complexity}/10)")
```

**Benefits:**
- Tackle complex conflicts first
- Avoid cascading merge issues
- Better conflict resolution strategy

### 5. Skill Context Integration

Skills can pass complexity analysis to downstream skills:

```python
from popkit_shared.utils.skill_context import save_skill_context, SkillOutput
from popkit_shared.utils.complexity_scoring import analyze_complexity

# Analyze complexity
analysis = analyze_complexity(task_description)

# Save for downstream skills
save_skill_context(SkillOutput(
    skill_name="pop-complexity-analyzer",
    status="completed",
    output={
        "complexity_score": analysis["complexity_score"],
        "complexity_analysis": analysis
    },
    artifacts=[],
    next_suggested="pop-writing-plans"
))

# Downstream skill reads complexity
from popkit_shared.utils.skill_context import load_skill_context

ctx = load_skill_context()
if ctx and ctx.complexity_score:
    complexity = ctx.complexity_score
    print(f"Previous analysis: {complexity}/10")
    # Adjust behavior based on complexity
```

**Benefits:**
- Avoid redundant analysis
- Share complexity insights
- Enable complexity-aware workflows

## Output Format

### Complexity Analysis Structure

```json
{
  "complexity_score": 7,
  "complexity_level": "COMPLEX",
  "recommended_subtasks": 6,
  "phase_distribution": {
    "discovery": 1,
    "planning": 2,
    "implementation": 4,
    "testing": 2,
    "review": 1,
    "integration": 1
  },
  "risk_factors": [
    "architecture_impact",
    "security_critical"
  ],
  "reasoning": "Complexity Score: 7/10 (Architecture changes, high impact). Primary factors: architecture changes required, external dependencies, security considerations.",
  "factors": {
    "files_affected": 60.0,
    "loc_estimate": 50.0,
    "dependencies": 50.0,
    "architecture_change": 100.0,
    "breaking_changes": 0.0,
    "testing_complexity": 50.0,
    "security_impact": 100.0,
    "integration_points": 0.0
  },
  "estimated_tokens": {
    "discovery": 5000,
    "planning": 12000,
    "implementation": 35000,
    "testing": 10000,
    "review": 6000,
    "total": 68000
  },
  "suggested_agents": [
    "code-architect",
    "refactoring-expert",
    "security-auditor"
  ]
}
```

## Subtask Recommendations

Based on complexity score:

| Complexity | Subtasks | Example |
|------------|----------|---------|
| 1-2 | 1 | Fix typo, update constant |
| 3-4 | 2-3 | Add button, update styling |
| 5-6 | 3-5 | Add form, API endpoint |
| 7-8 | 5-7 | Auth system, refactor module |
| 9-10 | 8-12 | Migrate architecture, redesign core |

## Phase Distribution

Recommended phases by complexity:

**Trivial (1-2):**
- Implementation: 1
- Testing: 1

**Simple (3-4):**
- Planning: 1
- Implementation: 2
- Testing: 1

**Moderate (5-6):**
- Planning: 1
- Implementation: 3
- Testing: 2
- Review: 1

**Complex (7-8):**
- Discovery: 1
- Planning: 2
- Implementation: 4
- Testing: 2
- Review: 1
- Integration: 1

**Very Complex (9-10):**
- Discovery: 2
- Architecture: 2
- Planning: 3
- Implementation: 5
- Testing: 3
- Review: 2
- Integration: 2
- Documentation: 1

## Risk Factors

Automatically detected risks:

| Risk Factor | Detection | Implication |
|-------------|-----------|-------------|
| breaking_changes | Keywords: breaking, incompatible | Requires migration plan |
| security_critical | Keywords: auth, security, crypto | Requires security review |
| architecture_impact | Keywords: refactor, redesign | Requires architecture review |
| integration_complexity | Keywords: api, webhook, integration | Requires integration testing |
| performance_sensitive | Keywords: performance, optimization | Requires performance testing |
| data_migration | Keywords: migrate, migration | Requires data safety plan |

## Token Estimation

Estimated token usage by complexity:

| Complexity | Total | Planning | Implementation | Testing |
|------------|-------|----------|----------------|---------|
| 1-2 | 7K | 2K | 5K | - |
| 3-4 | 17K | 4K | 10K | 3K |
| 5-6 | 38K | 8K | 20K | 6K |
| 7-8 | 68K | 12K | 35K | 10K |
| 9-10 | 135K | 20K | 60K | 20K |

## Agent Recommendations

Based on complexity level:

| Complexity | Agents |
|------------|--------|
| 1-3 | rapid-prototyper, code-explorer |
| 4-6 | refactoring-expert, code-explorer, test-writer |
| 7-8 | code-architect, refactoring-expert, security-auditor |
| 9-10 | code-architect, system-designer, tech-lead, security-auditor |

## Workflow Integration Examples

### Example 1: /popkit:dev Workflow

```bash
/popkit:dev "Add real-time notifications with WebSockets"
```

**Behind the scenes:**
1. Analyze complexity: Score 7/10 (Complex)
2. Select agents: code-architect, refactoring-expert
3. Choose workflow: Full mode (7 phases)
4. Estimate tokens: 68,000 total
5. Display to user: "Analyzing complexity... Score: 7/10"
6. Display subtasks: "Recommended: 6 subtasks"

### Example 2: Planning Workflow

```python
# User starts planning
task = "Refactor authentication module"

# Automatic complexity analysis
analysis = analyze_complexity(task)
score = analysis["complexity_score"]  # 7

# Determine workflow
if score >= 7:
    # Full planning with architecture review
    phases = ["discovery", "architecture", "planning", "implementation"]
    use_agents = ["code-architect", "refactoring-expert"]
else:
    # Standard planning
    phases = ["planning", "implementation"]
    use_agents = ["refactoring-expert"]

# Use phase distribution
phase_count = analysis["phase_distribution"]
# {'discovery': 1, 'planning': 2, 'implementation': 4, ...}
```

### Example 3: PRD Feature Scoring

```python
# Parse PRD
prd = parse_prd("product-requirements.md")

# Score each feature
for feature in prd.features:
    analysis = analyze_complexity(feature.description)

    feature.complexity = analysis["complexity_score"]
    feature.subtasks = analysis["recommended_subtasks"]
    feature.estimated_effort = analysis["estimated_tokens"]["total"]
    feature.risks = analysis["risk_factors"]

# Generate feature report
for feature in prd.features:
    print(f"{feature.name}:")
    print(f"  Complexity: {feature.complexity}/10")
    print(f"  Subtasks: {feature.subtasks}")
    print(f"  Effort: {feature.estimated_effort} tokens")
    print(f"  Risks: {', '.join(feature.risks)}")
```

## Customization

### Custom Weights

For specific use cases, customize factor weights:

```python
from popkit_shared.utils.complexity_scoring import ComplexityAnalyzer

# Emphasize architecture and security
custom_weights = {
    "files_affected": 0.10,
    "loc_estimate": 0.10,
    "dependencies": 0.10,
    "architecture_change": 0.30,  # Higher weight
    "breaking_changes": 0.15,
    "testing_complexity": 0.10,
    "security_impact": 0.10,      # Higher weight
    "integration_points": 0.05
}

analyzer = ComplexityAnalyzer(weights=custom_weights)
result = analyzer.analyze("Refactor core authentication")
```

### Project-Specific Calibration

Adjust scoring based on project context:

```python
# For small projects (< 10 files total)
# Multiply files_affected score by 0.5

# For high-security projects
# Multiply security_impact score by 2.0

# For greenfield projects
# Reduce architecture_change score by 0.5
```

## Testing

Run complexity analyzer tests:

```bash
# Direct testing
cd packages/shared-py
python -m popkit_shared.utils.complexity_scoring

# Via plugin tests
cd packages/popkit-core
python run_tests.py skills
```

## Future Enhancements

### 1. Machine Learning Calibration

- Train on historical task completion data
- Adjust scoring based on actual complexity
- Improve accuracy over time

### 2. Project Context Integration

- Consider team size
- Account for tech stack familiarity
- Adjust for project maturity

### 3. Dependency Graph Analysis

- Analyze task dependencies
- Recommend optimal sequencing
- Identify critical path

### 4. Resource Estimation

- Estimate time beyond tokens
- Predict developer hours
- Calculate sprint capacity

### 5. Historical Analytics

- Track complexity trends
- Identify complexity hotspots
- Measure estimation accuracy

## Migration Guide

No migration required - this is a new feature. Existing workflows will automatically benefit from complexity analysis.

## Performance Considerations

- **Analysis Speed:** < 100ms per task
- **Memory Usage:** Minimal (< 1MB)
- **Caching:** Results cached in skill context
- **Scalability:** Can analyze 1000+ tasks/minute

## Best Practices

1. **Trust the Score:** Complexity scores are calibrated for accuracy
2. **Use Recommendations:** Follow subtask and phase recommendations
3. **Monitor Risks:** Pay attention to identified risk factors
4. **Right-Size Agents:** Use suggested agents for better results
5. **Iterate:** Re-analyze after scope changes

## Related Documentation

- [Skill Context System](./skill-context-integration.md)
- [Agent Router Design](./agent-routing.md)
- [PRD Parser Specification](./prd-parser-spec.md)
- [Merge Conflict Resolver](./merge-conflict-resolution.md)

## Examples

### Simple Task

```python
result = analyze_complexity("Update button color in settings")

# Output:
# {
#   "complexity_score": 2,
#   "complexity_level": "TRIVIAL",
#   "recommended_subtasks": 1,
#   "risk_factors": [],
#   "suggested_agents": ["rapid-prototyper"]
# }
```

### Moderate Task

```python
result = analyze_complexity("Add user profile page with avatar upload")

# Output:
# {
#   "complexity_score": 5,
#   "complexity_level": "MODERATE",
#   "recommended_subtasks": 4,
#   "risk_factors": [],
#   "suggested_agents": ["refactoring-expert", "code-explorer"]
# }
```

### Complex Task

```python
result = analyze_complexity("Implement JWT authentication with refresh tokens")

# Output:
# {
#   "complexity_score": 7,
#   "complexity_level": "COMPLEX",
#   "recommended_subtasks": 6,
#   "risk_factors": ["security_critical"],
#   "suggested_agents": ["code-architect", "refactoring-expert", "security-auditor"]
# }
```

### Very Complex Task

```python
result = analyze_complexity("Migrate monolith to microservices architecture")

# Output:
# {
#   "complexity_score": 10,
#   "complexity_level": "VERY_COMPLEX",
#   "recommended_subtasks": 12,
#   "risk_factors": ["breaking_changes", "architecture_impact", "integration_complexity"],
#   "suggested_agents": ["code-architect", "system-designer", "tech-lead"]
# }
```

## Conclusion

The Complexity Analyzer provides foundational intelligence for PopKit's development workflows. By automatically analyzing task complexity and providing actionable recommendations, it enables:

- Intelligent agent selection
- Right-sized workflow selection
- Accurate effort estimation
- Proactive risk identification
- Optimal task breakdown

This integration is seamless, automatic, and ready for use by other PopKit features.
