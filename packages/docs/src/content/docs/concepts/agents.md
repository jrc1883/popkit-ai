---
title: Agent System
description: Understanding PopKit's tiered agent architecture
---

# Agent System

PopKit features a sophisticated tiered agent system with 31 specialized agents organized into three tiers.

## Agent Tiers

### Tier 1: Core Agents (Always Active)

These agents are always available and handle fundamental tasks:

- **code-editor**: Primary coding and file manipulation
- **documentation-maintainer**: Documentation updates and sync
- **git-expert**: Git operations and workflows
- **test-runner**: Test execution and validation

**Activation**: Always active in every session

### Tier 2: Context Agents (Auto-activated)

Activated automatically based on session context:

- **api-designer**: REST API design and implementation
- **code-reviewer**: Code quality analysis and reviews
- **deployment-engineer**: Deployment and CI/CD
- **security-auditor**: Security scanning and fixes

**Activation**: Triggered by file types, commands, or context

### Tier 3: Specialist Agents (On-demand)

Activated explicitly for specialized tasks:

- **performance-optimizer**: Performance profiling and optimization
- **database-architect**: Database design and migrations
- **ui-ux-designer**: Frontend design and user experience
- **devops-specialist**: Infrastructure and operations

**Activation**: Manual via commands or Power Mode

## How Agents Work

Agents in PopKit are:

1. **Specialized**: Each agent has a focused domain of expertise
2. **Contextual**: Agents activate based on project context
3. **Collaborative**: Agents can work together in Power Mode
4. **Configurable**: Agent behavior can be customized per project

## Agent Configuration

Agents are defined in `.claude-plugin/agents/` with:

- **Purpose**: What the agent does
- **Triggers**: When the agent activates
- **Tools**: What capabilities the agent has
- **Permissions**: What the agent can access

## Next Steps

- Learn about [Skills](/concepts/skills/)
- Explore [Commands](/concepts/commands/)
- Understand [Power Mode](/features/power-mode/)
