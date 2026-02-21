---
title: Skills
description: Reusable automation workflows in PopKit
---

# Skills

Skills are reusable automation workflows that encapsulate common development tasks. PopKit currently includes 44 skills across 4 plugins.

## What are Skills?

Skills in PopKit are:

- **Reusable**: Can be invoked from multiple contexts
- **Composable**: Can call other skills
- **Documented**: Include usage examples and parameters
- **Testable**: Have defined input/output contracts
- **Tiered**: Exposed directly (`/pop-*`) and through workflow commands (`/popkit-*`)

## Skill Categories

### Planning & Execution

- `pop-brainstorming`: Design exploration and specification refinement
- `pop-writing-plans`: Structured implementation plan generation
- `pop-executing-plans`: Controlled batch execution with checkpoints
- `pop-finish-branch`: End-of-work branch finalization flow

### Routines & Context

- `pop-morning`: Start-of-day health and readiness workflow
- `pop-nightly`: End-of-day cleanup and session capture workflow
- `pop-session-capture`: Persist working context for next session
- `pop-session-resume`: Restore previous context

### Quality & Operations

- `pop-assessment-security`: Security posture assessment
- `pop-code-review`: Risk-focused code review
- `pop-systematic-debugging`: Structured debugging methodology
- `pop-benchmark-runner`: Controlled benchmark and analysis runs

### Project & Platform

- `pop-analyze-project`: Architecture and pattern analysis
- `pop-project-init`: Project bootstrap and Claude config setup
- `pop-project-reference`: Cross-project context loading
- `pop-power-mode`: Multi-agent orchestration

## Using Skills

Skills can be invoked in several ways:

### From Commands

```bash
/popkit-dev:next
# Internally uses pop-next-action plus command-layer formatting/flow
```

### From Agents

Agents can invoke skills as part of their workflows.

### Directly (Advanced)

```bash
/pop-next-action
/pop-assessment-security
/skill invoke pop-next-action
```

Depending on Claude Code client version and settings, direct-skill entries may appear as bare `/pop-*` aliases or only via `/skill invoke`.

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
