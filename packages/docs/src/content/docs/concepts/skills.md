---
title: Skills
description: Reusable automation workflows in PopKit
---

# Skills

Skills are reusable automation workflows that encapsulate common development tasks. PopKit includes 68 skills across various categories.

## What are Skills?

Skills in PopKit:

- **Reusable**: Can be invoked from multiple contexts
- **Composable**: Can call other skills
- **Documented**: Include usage examples and parameters
- **Testable**: Have defined input/output contracts

## Skill Categories

### Development Workflows

- `pop-feature-dev`: 7-phase feature development
- `pop-brainstorming`: Design exploration and planning
- `pop-work-on-issue`: GitHub issue workflow

### Git Operations

- `pop-git-commit`: Smart commit message generation
- `pop-git-pr`: Pull request creation with context
- `pop-git-publish`: Public repository publishing

### Project Management

- `pop-next-action`: Context-aware next steps
- `pop-morning`: Morning routine and health check
- `pop-nightly`: End-of-day cleanup and summary

### Analysis & Quality

- `pop-code-review`: Comprehensive code review
- `pop-security-scan`: Security vulnerability detection
- `pop-performance-audit`: Performance profiling

## Using Skills

Skills can be invoked in several ways:

### From Commands

```bash
/popkit-dev:git commit
# Internally uses pop-git-commit skill
```

### From Agents

Agents can invoke skills as part of their workflows.

### Directly (Advanced)

```bash
/skill invoke pop-next-action
```

## Creating Custom Skills

Skills are defined in `SKILL.md` format with:

1. **Frontmatter**: Metadata and configuration
2. **Description**: What the skill does
3. **Usage**: How to use the skill
4. **Examples**: Real-world usage examples

See the [Custom Skills Guide](/guides/custom-skills/) for details.

## Next Steps

- Explore [Commands](/concepts/commands/)
- Learn about [Hooks](/concepts/hooks/)
- Create [Custom Skills](/guides/custom-skills/)
