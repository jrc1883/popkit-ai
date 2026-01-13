# Output Style Schemas

This directory contains JSON Schema definitions for PopKit agent output validation.

## Overview

Each agent in PopKit can declare an `output_style` in its frontmatter. The output-validator hook (`packages/popkit-core/hooks/output-validator.py`) validates agent outputs against these schemas to ensure consistent, structured output formats.

## Schema Format

All schemas follow JSON Schema Draft-07 format:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Schema Title",
  "description": "Description of the output format",
  "type": "object",
  "required": ["field1", "field2"],
  "properties": {
    "field1": {
      "type": "string",
      "description": "Field description"
    },
    "field2": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Score field (0-100)"
    }
  }
}
```

## Available Schemas

| Schema File                              | Output Style               | Used By Agent(s)              |
| ---------------------------------------- | -------------------------- | ----------------------------- |
| `accessibility-audit.schema.json`        | accessibility-audit        | accessibility-guardian        |
| `agent-handoff.schema.json`              | agent-handoff              | code-architect, code-explorer |
| `agent-specification.schema.json`        | agent-specification        | meta-agent                    |
| `analysis-report.schema.json`            | analysis-report            | researcher                    |
| `api-design-report.schema.json`          | api-design-report          | api-designer                  |
| `bundle-report.schema.json`              | bundle-report              | bundle-analyzer               |
| `code-optimization-report.schema.json`   | code-optimization-report   | dead-code-eliminator          |
| `code-review-report.schema.json`         | code-review-report         | code-reviewer                 |
| `conflict-resolution-report.schema.json` | conflict-resolution-report | merge-conflict-resolver       |
| `debugging-report.schema.json`           | debugging-report           | bug-whisperer                 |
| `deployment-report.schema.json`          | deployment-report          | deployment-validator          |
| `documentation-report.schema.json`       | documentation-report       | documentation-maintainer      |
| `migration-report.schema.json`           | migration-report           | migration-specialist          |
| `performance-report.schema.json`         | performance-report         | performance-optimizer         |
| `power-mode-checkin.schema.json`         | power-mode-checkin         | power-coordinator             |
| `prioritization-report.schema.json`      | prioritization-report      | feature-prioritizer           |
| `prototype-report.schema.json`           | prototype-report           | rapid-prototyper              |
| `refactoring-report.schema.json`         | refactoring-report         | refactoring-expert            |
| `rollback-report.schema.json`            | rollback-report            | rollback-specialist           |
| `security-audit-report.schema.json`      | security-audit-report      | security-auditor              |
| `structured-planning.schema.json`        | structured-planning        | prd-parser                    |
| `testing-report.schema.json`             | testing-report             | test-writer-fixer             |

## Field Extraction

The output-validator hook extracts fields from markdown-formatted agent outputs using regex patterns. Common fields include:

### Standard Fields

- `status` - Current status of the work
- `summary` - Summary section (extracted from `### Summary`)
- `recommendation` - Recommendations for next steps
- `date` - Date of the report

### Specialized Fields

- `from`, `to`, `task` - Handoff fields (agent-handoff)
- `severity` - Issue severity (debugging-report, security-audit-report, etc.)
- `confidence` - Confidence score 0-100 (agent-handoff, various reports)
- `healthScore` - Health score 0-100 (deployment-report)
- `securityScore` - Security score 0-100 (security-audit-report, accessibility-audit)
- `issueTitle` - Bug/issue title (debugging-report)
- `projectName` - Project name (analysis-report, security-audit-report)
- `symptom` - Bug symptom description (debugging-report)
- `scope` - Scope of work (analysis-report, structured-planning)

## Validation Process

1. Agent completes work and outputs markdown
2. SubagentStop hook triggers output-validator
3. Validator loads appropriate schema based on agent's `output_style`
4. Markdown output is parsed for structured fields
5. Extracted fields are validated against schema requirements
6. Validation result includes:
   - `status`: "valid", "invalid", "warning", or "skip"
   - `confidence`: 0-100% based on required field presence
   - `missing_fields`: List of required fields not found
   - `extracted_fields`: List of fields successfully extracted

## Adding New Schemas

When creating a new agent with a custom output format:

1. Create a new `.schema.json` file in this directory
2. Follow the JSON Schema Draft-07 format
3. Define `required` fields that must be present
4. Document all `properties` with descriptions
5. Add the `output_style` field to the agent's frontmatter
6. Update this README with the new schema mapping

## Testing

Test schema loading and validation:

```bash
# Test schema loading
python test-schema-loading.py

# Test validator integration
python test-validator-integration.py

# Test hook directly
echo '{"agent": "bug-whisperer", "output_style": "debugging-report", "output": "..."}' | \
  python packages/popkit-core/hooks/output-validator.py
```

## Design Principles

1. **Practical over Perfect**: Schemas focus on fields that can be reliably extracted from markdown
2. **Progressive Enhancement**: All schemas have minimal required fields, allowing agents flexibility
3. **Consistent Structure**: Common fields (summary, status, recommendation) appear across schemas
4. **Validation not Enforcement**: Validation provides guidance, not hard failures

## Version History

- **v1.0.0** (2026-01-11): Initial schema collection
  - 22 schemas covering all PopKit agents
  - Based on output-validator.py field extraction patterns
  - Aligned with existing agent output formats
