# Contributing to PopKit

Thank you for your interest in contributing to PopKit! We're excited to have you join our community of developers working to make AI-powered development workflows better for everyone.

This guide will help you get started with contributing to the PopKit plugin suite for Claude Code.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Process](#pull-request-process)
- [Plugin Development Guide](#plugin-development-guide)
- [Community and Support](#community-and-support)

---

## Code of Conduct

This project is committed to providing a welcoming and inclusive environment for all contributors. We expect all participants to treat each other with respect and professionalism.

Key principles:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

---

## Ways to Contribute

There are many ways to contribute to PopKit, and all contributions are valued:

### Bug Reports

Found a bug? Help us fix it!

1. Check if the issue already exists in [GitHub Issues](https://github.com/jrc1883/popkit-ai/issues)
2. Create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce the bug
   - Expected vs. actual behavior
   - Your environment (Claude Code version, OS, plugin version)
   - Screenshots or error messages (if applicable)

### Feature Requests

Have an idea for a new feature or improvement?

1. Check existing issues and discussions to avoid duplicates
2. Open a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Examples of how it would work
   - Any relevant alternatives you've considered

### Documentation Improvements

Documentation is crucial for a great developer experience:

- Fix typos or unclear explanations
- Add examples or tutorials
- Improve README files
- Create guides for common workflows
- Update outdated information

### Code Contributions

Ready to write code? Great! See the sections below for details on:

- Setting up your development environment
- Testing your changes
- Submitting pull requests

### Plugin Development

Want to create a new command, skill, or agent? See the [Plugin Development Guide](#plugin-development-guide) below.

---

## Getting Started

### Prerequisites

- **Claude Code**: Version 2.1.33+ recommended for full feature support
- **Python**: Python 3.x for running tests and hooks
- **Git**: For version control
- **GitHub Account**: To submit pull requests

### First-Time Contributors

If you're new to open source or PopKit:

1. Look for issues tagged with `good-first-issue` or `help-wanted`
2. Comment on the issue to let others know you're working on it
3. Ask questions! We're here to help
4. Start small - documentation fixes are a great way to get familiar with the project

---

## Development Setup

### 1. Fork and Clone the Repository

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/popkit-ai.git
cd popkit-ai
```

### 2. Install Plugins Locally

Install the plugins you want to work on from your local directory:

```bash
# Install individual plugins
/plugin install ./packages/popkit-core
/plugin install ./packages/popkit-dev
/plugin install ./packages/popkit-ops
/plugin install ./packages/popkit-research

# Or install all plugins
/plugin install ./packages/popkit-core
/plugin install ./packages/popkit-dev
/plugin install ./packages/popkit-ops
/plugin install ./packages/popkit-research
```

**Important**: After installing local plugins, restart Claude Code for changes to take effect.

### 3. Verify Installation

```bash
# Check that plugins are loaded
/plugin list

# Test a command to verify it's working
/popkit-dev:next
```

### 4. Make Changes

Edit files in the `packages/` directory:

```bash
# Plugin components are in each package directory
packages/
├── popkit-core/
│   ├── commands/       # Slash commands (*.md)
│   ├── skills/         # Reusable automation (SKILL.md)
│   ├── agents/         # Specialized AI agents (AGENT.md)
│   ├── hooks/          # Python hook scripts (*.py)
│   └── tests/          # Plugin tests
├── popkit-dev/
├── popkit-ops/
└── popkit-research/
```

### 5. Reload Changes

After making changes:

```bash
# Uninstall the local plugin
/plugin uninstall popkit-core

# Reinstall to pick up changes
/plugin install ./packages/popkit-core

# Restart Claude Code
```

---

## Testing

PopKit uses a comprehensive testing framework to ensure plugin quality and compatibility.

### Running Tests

#### Test All Plugins

```bash
# Navigate to popkit-core (contains test runner)
cd packages/popkit-core

# Run all tests for all plugins
python run_all_tests.py

# Run with verbose output
python run_all_tests.py --verbose
```

#### Test Individual Plugin

```bash
# Test only popkit-core
cd packages/popkit-core
python run_tests.py

# Test specific category
python run_tests.py hooks
python run_tests.py agents
python run_tests.py skills
```

#### Test via PopKit Commands

If you have PopKit installed:

```bash
# Run all tests
/popkit-core:plugin test

# Test specific category
/popkit-core:plugin test agents

# Verbose output
/popkit-core:plugin test --verbose
```

### Test Categories

- **agents**: Validates agent markdown format and frontmatter
- **hooks**: Tests hook JSON protocol and execution
- **skills**: Validates skill format and structure
- **structure**: Checks plugin integrity and required files
- **cross-plugin**: Tests cross-plugin compatibility

### Before Submitting

Always run tests before submitting a pull request:

```bash
cd packages/popkit-core
python run_all_tests.py
```

Fix any failures before submitting your PR. If you're adding new functionality, consider adding tests to cover it.

---

## Commit Message Convention

PopKit uses [Conventional Commits](https://www.conventionalcommits.org/) for clear, structured commit messages.

### Format

```
<type>: <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or updates
- `chore`: Maintenance tasks (dependencies, configuration)
- `refactor`: Code changes that neither fix bugs nor add features
- `style`: Code style changes (formatting, whitespace)
- `perf`: Performance improvements

### Examples

```bash
# New feature
feat: add skill for automated dependency updates

# Bug fix
fix: correct path handling in Windows hook scripts

# Documentation
docs: update CONTRIBUTING.md with testing guidelines

# Tests
test: add validation for agent frontmatter format

# Chore
chore: update plugin version to 1.0.0-beta.4

# Multiple changes (use body for details)
feat: add deploy skill for Vercel

Add new deployment skill that handles Vercel deployments with
automatic environment configuration and health checks.

Closes #123
```

### Tips

- Use present tense ("add" not "added")
- Keep the first line under 72 characters
- Reference issues and PRs when relevant
- Be specific and descriptive

---

## Pull Request Process

### 1. Create a Feature Branch

```bash
# Create and switch to a new branch
git checkout -b feat/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Follow existing code patterns and conventions
- Update documentation as needed
- Add tests for new functionality
- Keep commits focused and atomic

### 3. Test Locally

```bash
# Run tests
cd packages/popkit-core
python run_all_tests.py

# Install locally and test in Claude Code
/plugin install ./packages/popkit-core
# Restart Claude Code and test your changes
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with conventional commit message
git commit -m "feat: add your feature description"
```

### 5. Push to Your Fork

```bash
git push origin feat/your-feature-name
```

### 6. Create Pull Request

1. Go to the [PopKit repository](https://github.com/jrc1883/popkit-ai)
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template with:
   - Clear description of changes
   - Related issues (use "Closes #123" to auto-close issues)
   - Testing performed
   - Screenshots (if UI changes)
   - Breaking changes (if any)

### 7. Code Review

- Respond to review feedback promptly
- Make requested changes in new commits
- Don't force-push after review has started
- Be open to suggestions and discussion

### 8. Merge

Once approved:

- Maintainers will merge your PR
- Your contribution will be included in the next release
- You'll be credited in the changelog

---

## Plugin Development Guide

### Plugin Architecture

PopKit uses a modular architecture with 5 focused plugins:

| Plugin              | Purpose                    | Key Components                           |
| ------------------- | -------------------------- | ---------------------------------------- |
| **popkit-core**     | Foundation & orchestration | Power Mode, project tools, config        |
| **popkit-dev**      | Development workflows      | Git, GitHub, routines, feature dev       |
| **popkit-ops**      | Operations & quality       | Testing, debugging, security, deployment |
| **popkit-research** | Knowledge management       | Research capture, knowledge base         |

### Plugin Structure

Each plugin package contains:

```
packages/popkit-dev/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── commands/
│   ├── git.md               # /popkit-dev:git command
│   └── routine.md           # /popkit-dev:routine command
├── skills/
│   ├── git-commit/
│   │   └── SKILL.md         # Git commit skill
│   └── feature-dev/
│       └── SKILL.md         # Feature development skill
├── agents/
│   ├── git-assistant/
│   │   └── AGENT.md         # Git operations agent
│   └── code-reviewer/
│       └── AGENT.md         # Code review agent
├── hooks/
│   ├── hooks.json           # Hook configuration
│   └── session-start.py     # Session start hook
└── tests/
    └── test_plugin.py       # Plugin tests
```

### Adding a New Command

Commands are markdown files with YAML frontmatter:

**File**: `packages/popkit-dev/commands/my-command.md`

```markdown
---
name: my-command
description: Brief description of what this command does
usage: |
  /popkit:my-command [options]

  Options:
    --option1    Description of option1
    --option2    Description of option2
examples:
  - /popkit:my-command --option1
  - /popkit:my-command --option2 value
---

# My Command

Detailed description of the command behavior and use cases.

## Implementation

[Command implementation instructions for Claude]
```

### Adding a New Skill

Skills are reusable automation patterns:

**File**: `packages/popkit-dev/skills/my-skill/SKILL.md`

```markdown
---
name: my-skill
description: Brief description of the skill
category: development
tags: [tag1, tag2]
---

# My Skill

## Purpose

What this skill does and when to use it.

## Usage

How to invoke and use the skill.

## Examples

Concrete examples of the skill in action.

## Implementation

[Skill implementation instructions for Claude]
```

### Adding a New Agent

Agents are specialized AI assistants:

**File**: `packages/popkit-dev/agents/my-agent/AGENT.md`

```markdown
---
name: my-agent
description: Brief description of the agent
triggers:
  - keyword1
  - keyword2
capabilities:
  - capability1
  - capability2
---

# My Agent

## Purpose

What this agent specializes in.

## When to Use

Situations where this agent should be invoked.

## Capabilities

Detailed list of what the agent can do.

## Instructions

[Agent behavior instructions for Claude]
```

### Hook Standards

All hooks must follow Claude Code portability standards:

#### Path Handling

```json
{
  "type": "command",
  "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/my-hook.py\"",
  "timeout": 10000
}
```

Key requirements:

- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- Double-quote paths for Windows compatibility
- Use forward slashes for cross-platform support
- Python shebang: `#!/usr/bin/env python3`

#### JSON Protocol

Hooks communicate via JSON stdin/stdout:

**Input** (stdin):

```json
{
  "event": "session-start",
  "context": {
    "workspace": "/path/to/project"
  }
}
```

**Output** (stdout):

```json
{
  "success": true,
  "message": "Hook executed successfully",
  "data": {
    "key": "value"
  }
}
```

#### Error Handling

```python
#!/usr/bin/env python3
import json
import sys

try:
    # Read input
    input_data = json.loads(sys.stdin.read())

    # Process
    result = do_something(input_data)

    # Output success
    output = {
        "success": True,
        "data": result
    }
    print(json.dumps(output))
    sys.exit(0)

except Exception as e:
    # Output error
    error = {
        "success": False,
        "error": str(e)
    }
    print(json.dumps(error))
    sys.exit(1)
```

### Best Practices

1. **Follow Existing Patterns**: Look at similar commands/skills/agents for reference
2. **Test Thoroughly**: Run all tests before submitting
3. **Document Well**: Clear descriptions, examples, and usage instructions
4. **Keep It Modular**: One command/skill/agent should do one thing well
5. **Cross-Platform**: Test on Windows, macOS, and Linux if possible
6. **No Build Step**: PopKit is configuration-only (no TypeScript/compilation)

---

## Community and Support

### Getting Help

- **Issues**: Browse [GitHub Issues](https://github.com/jrc1883/popkit-ai/issues) for questions and discussions
- **Documentation**: Check [CLAUDE.md](CLAUDE.md) for detailed development guide
- **README**: See [README.md](README.md) for user-facing documentation

### Asking Questions

When asking for help:

1. Search existing issues first
2. Provide context (what you're trying to do, what you've tried)
3. Include error messages and logs
4. Mention your environment (Claude Code version, OS)
5. Be patient and respectful

### Staying Updated

- Watch the repository for notifications
- Check [CHANGELOG.md](CHANGELOG.md) for release notes
- Follow issue discussions for roadmap updates

---

## Recognition

All contributors will be:

- Listed in release notes for their contributions
- Credited in the changelog
- Acknowledged in the community

Thank you for contributing to PopKit and helping make AI-powered development workflows better for everyone!

---

## Questions?

If you have any questions about contributing, feel free to:

- Open an issue with the `question` label
- Reach out to the maintainer: Joseph Cannon <joseph@thehouseofdeals.com>

**Happy contributing!**
