# Contributing to PopKit

Thank you for your interest in contributing to PopKit! This guide will help you get started.

## Repository Structure

PopKit uses a **split-repo model**:

| Repository | Visibility | Contents |
|------------|------------|----------|
| `jrc1883/popkit` | Private | Full monorepo (plugin + cloud) |
| `jrc1883/popkit-claude` | **Public** | Claude Code plugin (install target) |

Users install from the public repo, but development happens in the private monorepo.

## Getting Started

### Prerequisites

- [Claude Code](https://claude.ai/code) installed
- Git
- GitHub CLI (`gh`)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jrc1883/popkit.git
   cd popkit
   ```

2. **Install PopKit for development**
   ```
   /plugin marketplace add jrc1883/popkit-claude
   /plugin install popkit@popkit-claude
   ```

3. **Restart Claude Code** to load the plugin

4. **Verify installation**
   ```
   /popkit:plugin test
   ```

## Project Structure

```
packages/
  plugin/                  Claude Code plugin (main package)
    .claude-plugin/        Plugin manifest
    agents/                30 agent definitions
      tier-1-always-active/  11 core agents
      tier-2-on-demand/    17 specialized agents
      feature-workflow/    Development workflow agents
    skills/                36 reusable skills
    commands/              18 slash commands
    hooks/                 Python hooks (JSON stdin/stdout)
      utils/               Utility modules
    output-styles/         Output format templates
    power-mode/            Multi-agent orchestration
    templates/             MCP server template
  cloud/                   PopKit Cloud API
```

## Development Workflow

### 1. Find an Issue

Check [GitHub Issues](https://github.com/jrc1883/popkit-claude/issues) for:
- Issues labeled `good-first-issue` for newcomers
- Issues in the current milestone
- Issues labeled with your area of interest

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Or use PopKit:
```
/popkit:worktree create feature/your-feature-name
```

### 3. Make Changes

PopKit is primarily **configuration-only** - no build step required:
- Markdown files with YAML frontmatter (skills, commands, agents)
- JSON configuration files
- Python scripts for hooks

### 4. Test Your Changes

```
/popkit:plugin test           # Run all tests
/popkit:plugin test hooks     # Test hook JSON protocol
/popkit:plugin test routing   # Verify agent selection
```

### 5. Commit

Use conventional commits:
```
/popkit:git commit "feat(commands): add new subcommand"
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

### 6. Create a Pull Request

```
/popkit:git pr
```

Or use GitHub CLI:
```bash
gh pr create --title "feat: your feature" --body "Description"
```

## Contribution Types

### Adding a Command

1. Create `packages/plugin/commands/your-command.md`
2. Add YAML frontmatter with description
3. Document usage, examples, and integration

### Adding a Skill

1. Create `packages/plugin/skills/your-skill/SKILL.md`
2. Follow the skill template format
3. Document triggers and workflows

### Adding an Agent

1. Create directory in appropriate tier:
   - `agents/tier-1-always-active/` for core agents
   - `agents/tier-2-on-demand/` for specialized agents
2. Add `AGENT.md` following the template
3. Update `agents/config.json` with routing rules

### Improving Documentation

- Update relevant markdown files
- Keep CLAUDE.md in sync with changes
- Add examples and use cases

## Code Style

### Markdown Files

- Use YAML frontmatter for metadata
- Include clear examples
- Document integration points

### Python Hooks

- Use `#!/usr/bin/env python3`
- JSON stdin/stdout protocol
- Stateless operation where possible

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
<type>(<scope>): <subject>

<body>

<footer>
```

All commits include Claude attribution:
```
Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Testing

### Plugin Tests

```
/popkit:plugin test
```

Validates:
- Plugin structure
- Hook JSON protocol
- Agent routing rules
- Skill definitions

### Self-Assessment

```
/popkit:assess all
```

Runs all assessor agents:
- Anthropic compliance
- Security audit
- Performance check
- UX review
- Architecture review
- Documentation audit

## Pull Request Guidelines

### Before Submitting

- [ ] All plugin tests pass
- [ ] Self-assessment shows no critical issues
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional format

### PR Template

```markdown
## Summary
<Brief description of changes>

## Changes
- `file.ts`: <what changed>

## Test Plan
- [ ] Plugin tests pass
- [ ] Manual testing completed

## Related Issues
Closes #<issue-number>
```

## Getting Help

- **Questions:** Open a [Discussion](https://github.com/jrc1883/popkit-claude/discussions)
- **Bugs:** Open an [Issue](https://github.com/jrc1883/popkit-claude/issues)
- **Feature Requests:** Use the feature request template

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the project's license.

---

## See Also

- [[Home]] - Getting started
- [[Commands]] - Command reference
- [[Agents]] - Agent catalog
