---
title: Agent Configuration
description: Configuring and customizing PopKit agents
---

# Agent Configuration

Learn how to configure, customize, and create agents for PopKit workflows.

## Agent Structure

Agents are defined in `AGENT.md` format with:

1. **Frontmatter**: YAML metadata and configuration
2. **Purpose**: Agent's role and responsibilities
3. **Triggers**: When the agent activates
4. **Tools**: Permissions and capabilities

## Basic Agent Template

```markdown
---
name: my-agent
description: Brief description of agent role
tier: 2
triggers:
  - keyword: authentication
  - file_pattern: "**/*auth*.js"
tools:
  - Read
  - Write
  - Grep
---

# Agent Name

## Purpose

Clear description of what this agent does and when to use it.

## Triggers

Conditions that activate this agent:
- Keyword mentions
- File patterns
- Commands
- Context

## Capabilities

What the agent can do:
- Specific tasks
- Domain expertise
- Tools available
```

## Agent Tiers

### Tier 1: Core Agents

```yaml
tier: 1
```

**Characteristics**:
- Always active
- Fundamental tasks
- Broad capabilities
- Examples: code-editor, git-expert

### Tier 2: Context Agents

```yaml
tier: 2
```

**Characteristics**:
- Auto-activated by context
- Specialized domains
- Moderate capabilities
- Examples: api-designer, security-auditor

### Tier 3: Specialist Agents

```yaml
tier: 3
```

**Characteristics**:
- Manually activated
- Highly specialized
- Narrow focus
- Examples: performance-optimizer, database-architect

## Trigger Configuration

### Keyword Triggers

```yaml
triggers:
  - keyword: authentication
  - keyword: oauth
  - keyword: login
```

Agent activates when these keywords appear in user messages.

### File Pattern Triggers

```yaml
triggers:
  - file_pattern: "**/*auth*.{js,ts}"
  - file_pattern: "src/security/**/*"
```

Agent activates when matching files are opened or modified.

### Command Triggers

```yaml
triggers:
  - command: "/security"
  - command: "/audit"
```

Agent activates for specific commands.

### Context Triggers

```yaml
triggers:
  - context: security_review
  - context: code_review
```

Agent activates for specific workflow contexts.

## Tool Permissions

### Basic Tools

```yaml
tools:
  - Read          # Read files
  - Write         # Write files
  - Grep          # Search files
  - Glob          # Find files
  - Edit          # Edit files
```

### Bash Permissions

```yaml
tools:
  - Bash(git status)           # Exact command
  - Bash(git log*)             # Git log with any args
  - Bash(npm test*)            # Any npm test command
  - Bash(pytest *)             # Any pytest command
```

### MCP Wildcards

```yaml
tools:
  - mcp__server__*             # All tools from MCP server
```

## Configuration Files

### Global Agent Config

`.popkit/agents.json`:

```json
{
  "enabled": true,
  "tiers": {
    "1": { "always_active": true },
    "2": { "auto_activate": true },
    "3": { "manual_only": true }
  },
  "agents": {
    "code-editor": {
      "enabled": true,
      "priority": 100
    }
  }
}
```

### Project Agent Config

`.claude/agents.json`:

```json
{
  "project_agents": [
    "security-auditor",
    "api-designer"
  ],
  "disabled_agents": [
    "ui-ux-designer"
  ]
}
```

## Creating Custom Agents

### 1. Choose Agent Tier

Decide tier based on frequency of use:
- Tier 1: Daily use
- Tier 2: Weekly use
- Tier 3: Occasional use

### 2. Define Triggers

Specify when agent should activate:
- Keywords in user messages
- File patterns
- Commands
- Context

### 3. Set Tool Permissions

List only tools the agent needs:
- Be conservative
- Use wildcards for Bash
- Request only necessary permissions

### 4. Write Clear Purpose

Explain:
- What the agent does
- When to use it
- What it doesn't do

### 5. Test Thoroughly

Test agent:
- Triggers activate correctly
- Tools work as expected
- Permissions are sufficient
- No conflicts with other agents

## Example: Custom Database Agent

```markdown
---
name: postgres-expert
description: PostgreSQL database administration and optimization
tier: 3
triggers:
  - keyword: postgres
  - keyword: database
  - file_pattern: "**/*.sql"
  - file_pattern: "**/migrations/**/*"
tools:
  - Read
  - Write
  - Grep
  - Bash(psql *)
  - Bash(pg_dump *)
---

# PostgreSQL Expert

## Purpose

Specialized agent for PostgreSQL database design, migrations, optimization, and administration.

## Triggers

Activated when:
- User mentions "postgres" or "database"
- SQL files are opened or modified
- Migration files are accessed
- Database-related commands are used

## Capabilities

### Database Design
- Schema design and normalization
- Index optimization
- Query performance tuning

### Migrations
- Create migration scripts
- Review migration safety
- Rollback strategies

### Administration
- Backup and restore
- User permissions
- Configuration tuning

## Tools

- Read/Write: SQL files and migrations
- Grep: Search database code
- psql: Execute queries (read-only)
- pg_dump: Backup operations
```

## Best Practices

1. **Single Responsibility**: One clear purpose per agent
2. **Minimal Permissions**: Only tools needed
3. **Clear Triggers**: Specific, non-overlapping
4. **Good Names**: Descriptive, role-based
5. **Test Thoroughly**: Verify activation and behavior
6. **Document Well**: Clear purpose and usage

## Troubleshooting

### Agent Not Activating

**Symptom**: Agent doesn't activate when expected

**Solution**:
- Check trigger conditions
- Verify agent is enabled
- Check tier configuration
- Review logs for conflicts

### Permission Errors

**Symptom**: Agent can't access tools

**Solution**:
- Add required tools to `tools` list
- Use wildcard Bash patterns
- Check MCP permissions

### Agent Conflicts

**Symptom**: Multiple agents responding

**Solution**:
- Make triggers more specific
- Adjust agent priorities
- Disable conflicting agents

## Next Steps

- Learn about [Hook Development](/guides/hooks/)
- Review [Custom Skills](/guides/custom-skills/)
- Explore existing agents in PopKit packages
