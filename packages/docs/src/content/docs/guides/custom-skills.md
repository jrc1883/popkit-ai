---
title: Creating Custom Skills
description: Guide to building your own PopKit skills
---

# Creating Custom Skills

Learn how to create custom skills that extend PopKit's capabilities for your specific workflows.

## Skill Structure

Skills are defined in `SKILL.md` format with three main sections:

1. **Frontmatter**: YAML metadata
2. **Description**: What the skill does
3. **Implementation**: Instructions for Claude

## Basic Skill Template

```markdown
---
name: my-custom-skill
description: Brief description of what the skill does
category: custom
version: 1.0.0
---

# My Custom Skill

Detailed description of the skill's purpose and use cases.

## Usage

How to invoke and use the skill.

## Implementation

Detailed step-by-step instructions for Claude to execute the skill.

## Examples

Real-world usage examples.
```

## Skill Categories

Organize skills into categories:

- `core`: Fundamental operations
- `git`: Git and version control
- `analysis`: Code analysis and inspection
- `workflow`: Development workflows
- `custom`: User-defined skills

## Frontmatter Options

```yaml
---
name: skill-name # Required: Unique identifier
description: Short description # Required: One-line summary
category: custom # Required: Category name
version: 1.0.0 # Required: Semantic version
author: Your Name # Optional: Creator name
context: fork # Optional: Run in isolated context
tools: # Optional: Tool permissions
  - Read
  - Write
  - Bash(npm test*)
---
```

## Adding Tool Permissions

Control what the skill can do:

```yaml
tools:
  - Read # Read files
  - Write # Write files
  - Grep # Search files
  - Glob # Find files
  - Bash(git status) # Exact command
  - Bash(npm test*) # Command with args
  - Bash(pytest *) # Any pytest command
```

## Forked Context Skills

For expensive operations, use forked context:

```yaml
---
name: expensive-analysis
description: Deep code analysis
context: fork # Runs in isolated context
---
```

**When to use fork**:

- Embedding generation
- Large-scale analysis
- Web research
- One-time operations

## Skill Installation

### Local Skills (Project-Specific)

Create in `.claude/skills/`:

```bash
.claude/
└── skills/
    └── my-skill/
        └── SKILL.md
```

### Plugin Skills (Reusable)

Create in plugin package:

```bash
packages/my-plugin/
└── skills/
    └── my-skill/
        └── SKILL.md
```

## Testing Skills

### Manual Testing

```bash
/skill invoke my-custom-skill
```

### Automated Testing

Create test file in `skills/tests/`:

```python
def test_my_skill():
    """Test skill functionality"""
    # Test implementation
    assert skill_works()
```

## Best Practices

1. **Clear Names**: Use descriptive, hyphenated names
2. **Good Descriptions**: One-line summary of purpose
3. **Detailed Instructions**: Step-by-step for Claude
4. **Real Examples**: Show actual usage scenarios
5. **Minimal Permissions**: Only request tools needed
6. **Version Control**: Use semantic versioning
7. **Test Thoroughly**: Verify skill works as expected

## Example: Custom Code Review Skill

```markdown
---
name: review-security
description: Security-focused code review
category: analysis
version: 1.0.0
tools:
  - Read
  - Grep
  - Bash(grep -r *)
---

# Security Code Review

Performs security-focused code review looking for common vulnerabilities.

## Usage

Invoke this skill when reviewing code for security issues:

\`\`\`bash
/skill invoke review-security
\`\`\`

## Implementation

1. **Scan for Sensitive Data**
   - Search for API keys, tokens, passwords
   - Check for hardcoded credentials
   - Look for exposed secrets

2. **Check Input Validation**
   - Identify user input points
   - Verify sanitization
   - Check for SQL injection risks

3. **Review Authentication**
   - Check authentication logic
   - Verify authorization checks
   - Look for session issues

4. **Generate Report**
   - List vulnerabilities found
   - Prioritize by severity
   - Suggest fixes

## Examples

\`\`\`bash

# Review current changes

/skill invoke review-security

# Review specific file

/skill invoke review-security src/auth.js
\`\`\`
```

## Next Steps

- Learn about [Agent Configuration](/guides/agent-config/)
- Explore [Hook Development](/guides/hooks/)
- Review existing skills in PopKit packages

## Troubleshooting

### Skill Not Found

**Symptom**: `/skill invoke` says skill doesn't exist

**Solution**:

- Check file name is `SKILL.md`
- Verify frontmatter `name` field
- Ensure in `.claude/skills/` or plugin `skills/` directory
- Restart Claude Code (for plugin skills)

### Permission Errors

**Symptom**: Skill can't access tools

**Solution**:

- Add required tools to `tools` field
- Use wildcard patterns: `Bash(command *)`
- Check tool names match exactly

### Context Issues

**Symptom**: Skill loses context or runs slowly

**Solution**:

- Consider using `context: fork`
- Reduce tool permissions
- Optimize implementation steps
