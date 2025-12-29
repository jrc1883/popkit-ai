# PopKit v1.0.0-beta.1 Beta Testing Guide

**Welcome Beta Testers!** 🎉

Thank you for participating in the PopKit v1.0.0-beta.1 beta program. This guide will help you install, test, and provide valuable feedback on the new modular architecture.

---

## Table of Contents

1. [What's New in v1.0.0-beta.1](#whats-new)
2. [Installation](#installation)
3. [Testing Focus Areas](#testing-focus-areas)
4. [How to Provide Feedback](#feedback)
5. [Known Limitations](#known-limitations)
6. [Troubleshooting](#troubleshooting)

---

## What's New in v1.0.0-beta.1 {#whats-new}

PopKit has been transformed from a monolithic plugin into **5 focused workflow plugins**:

### The Five Plugins

| Plugin | Purpose | Best For |
|--------|---------|----------|
| **popkit-core** | Foundation & Power Mode | All users (required) |
| **popkit-dev** | Development workflows | Daily development, git operations |
| **popkit-ops** | Operations & quality | Testing, debugging, deployment |
| **popkit-research** | Knowledge management | Research, documentation |
| **popkit-suite** | Complete bundle | One-click install (all features) |

### Key Changes

- ✅ **Modular Architecture**: Install only what you need
- ✅ **Shared Foundation**: `popkit-shared` v1.0.0 (70 utility modules)
- ✅ **100% Test Coverage**: All 31/31 tests passing
- ✅ **Same Commands**: All `/popkit:*` commands work identically
- ✅ **Cleaner Structure**: 12 packages (down from 15)

---

## Installation {#installation}

### Prerequisites

- **Claude Code**: Version 2.0.67+ (required for extended thinking, plan mode)
- **Python**: 3.8+ (for hooks and scripts)
- **Git**: For version control features

### Option 1: Complete Suite (Recommended for Beta Testing)

Install all plugins at once:

```bash
/plugin install popkit-suite@jrc1883/popkit-claude
```

After installation, **restart Claude Code**.

### Option 2: Selective Installation

Install specific plugins based on your needs:

```bash
# Core (required)
/plugin install popkit-core@jrc1883/popkit-claude

# Development workflows
/plugin install popkit-dev@jrc1883/popkit-claude

# Operations & quality
/plugin install popkit-ops@jrc1883/popkit-claude

# Knowledge management
/plugin install popkit-research@jrc1883/popkit-claude
```

After installation, **restart Claude Code**.

### Verification

After restart, verify installation:

```
/popkit:plugin test
```

Expected output: Test results showing plugin structure, hooks, skills, and agents are working.

---

## Testing Focus Areas {#testing-focus-areas}

### Critical Path Testing (All Beta Testers)

These are the **must-test** workflows:

#### 1. Morning Routine
```
/popkit:routine morning
```

**What to test:**
- ✅ Does it analyze your project correctly?
- ✅ Is the "Ready to Code" score accurate?
- ✅ Are all health checks relevant?
- ✅ Does the ASCII dashboard render properly?

#### 2. Feature Development
```
/popkit:dev "add user authentication"
```

**What to test:**
- ✅ Does it understand your project architecture?
- ✅ Are the implementation steps clear and accurate?
- ✅ Does it handle errors gracefully?
- ✅ Does the review phase catch issues?

#### 3. Git Operations
```
/popkit:git commit
/popkit:git pr
/popkit:git review
```

**What to test:**
- ✅ Are commit messages well-formatted?
- ✅ Does PR creation work smoothly?
- ✅ Is code review helpful and actionable?

#### 4. Power Mode (Advanced)
```
/popkit:power init
/popkit:power start
```

**What to test:**
- ✅ Does native async mode work without Redis?
- ✅ Can multiple agents coordinate properly?
- ✅ Does the status line show accurate info?

### Plugin-Specific Testing

#### popkit-core
- `/popkit:project analyze` - Project analysis
- `/popkit:project init` - Project initialization
- `/popkit:plugin test` - Plugin integrity tests

#### popkit-dev
- `/popkit:dev` - Full 7-phase development
- `/popkit:git` - All git subcommands
- `/popkit:routine` - Morning/nightly routines
- `/popkit:next` - Next action recommendations

#### popkit-ops
- `/popkit:assess all` - Quality assessments
- `/popkit:audit health` - Health audits
- `/popkit:debug code` - Debugging workflows
- `/popkit:security scan` - Security scanning

#### popkit-research
- `/popkit:research capture` - Research capture
- `/popkit:knowledge search` - Knowledge base search

### Edge Cases to Test

1. **Large Projects** (1000+ files):
   - Does morning routine complete in reasonable time?
   - Are embeddings efficient?

2. **Monorepos**:
   - Can PopKit detect and work with multiple projects?
   - Does dashboard mode work?

3. **Non-Standard Structures**:
   - Projects without package.json
   - Projects with custom build systems
   - Projects with nested workspaces

4. **Error Handling**:
   - What happens with no internet connection?
   - How does it handle missing dependencies?
   - Does it recover gracefully from failures?

---

## How to Provide Feedback {#feedback}

### Feedback Channels

**Primary**: GitHub Issues
https://github.com/jrc1883/popkit/issues

**For Bugs**: Use the template in [BETA_FEEDBACK_TEMPLATE.md](./BETA_FEEDBACK_TEMPLATE.md)

**For Feature Requests**: Label with `enhancement` and `beta-feedback`

### What We're Looking For

#### High Priority Feedback

1. **Breaking Issues**:
   - Commands that don't work
   - Installation failures
   - Data loss or corruption
   - Security vulnerabilities

2. **Usability Problems**:
   - Confusing workflows
   - Unclear error messages
   - Missing documentation
   - Performance bottlenecks

3. **Architecture Feedback**:
   - Is the modular split helpful?
   - Should plugins be combined differently?
   - Are dependencies clear?

#### Nice-to-Have Feedback

1. **Feature Ideas**:
   - New commands or skills
   - Workflow improvements
   - Integration opportunities

2. **Documentation Gaps**:
   - Missing examples
   - Unclear explanations
   - Outdated information

### Feedback Template

When reporting issues, please include:

```markdown
## Issue Description
[What went wrong?]

## Steps to Reproduce
1.
2.
3.

## Expected Behavior
[What should happen?]

## Actual Behavior
[What actually happened?]

## Environment
- Claude Code Version:
- PopKit Version: v1.0.0-beta.1
- Plugins Installed: [popkit-core, popkit-dev, ...]
- OS: [Windows/Mac/Linux]
- Project Type: [Next.js, Python, etc.]

## Screenshots/Logs
[If applicable]
```

---

## Known Limitations {#known-limitations}

### Expected Issues (Being Worked On)

1. **Context Usage**: Modular architecture uses ~15.3k tokens baseline (improved from 25.7k)
2. **First-Time Setup**: Initial embedding generation can take 1-2 minutes
3. **Power Mode**: Redis mode requires Docker (native async mode works without)
4. **Documentation**: Some package READMEs are still being updated

### Not Yet Implemented

1. **Cloud Features**: API key integration for enhanced semantic search
2. **Team Features**: Multi-user collaboration (planned for v2.0)
3. **Marketplace Submission**: Awaiting Claude Code marketplace approval

### By Design

1. **Restart Required**: Plugin installation requires Claude Code restart
2. **Python Dependency**: Hooks require Python 3.8+ (by Claude Code design)
3. **Git Requirement**: Most workflows require git repository

---

## Troubleshooting {#troubleshooting}

### Installation Issues

**Problem**: Plugin installation fails

**Solution**:
```bash
# Check Claude Code version
claude --version  # Should be 2.0.67+

# Try removing and reinstalling
/plugin uninstall popkit-suite@jrc1883/popkit-claude
/plugin install popkit-suite@jrc1883/popkit-claude
```

**Problem**: Commands not found after install

**Solution**:
1. Verify installation: `/plugin list`
2. Restart Claude Code completely
3. Check plugin directory exists: `ls ~/.claude/plugins/`

### Runtime Issues

**Problem**: Hooks not executing

**Solution**:
```bash
# Check Python version
python --version  # Should be 3.8+

# Verify hook scripts are executable
ls -la ~/.claude/plugins/popkit-*/hooks/*.py

# Check hook logs
cat ~/.claude/logs/hooks.log
```

**Problem**: Shared module import errors

**Solution**:
```bash
# Reinstall shared package
pip install --upgrade popkit-shared>=1.0.0

# Or install from local
cd ~/.claude/plugins/popkit-core/
pip install -e ../shared-py/
```

**Problem**: Performance issues

**Solution**:
1. Check context usage: Enable debug mode
2. Reduce enabled plugins: Install only what you need
3. Clear embedding cache: `rm -rf ~/.claude/cache/embeddings/`

### Getting Help

If you encounter issues not covered here:

1. **Check Documentation**: Read plugin READMEs
2. **Search Issues**: https://github.com/jrc1883/popkit/issues
3. **Ask Questions**: Create a new issue with `question` label
4. **Emergency**: Tag issue with `critical` for urgent problems

---

## Beta Testing Timeline

**Beta Period**: 4-8 weeks (January-February 2025)

**Milestones**:
- **Week 1-2**: Critical bug fixes, installation issues
- **Week 3-4**: Usability improvements, documentation updates
- **Week 5-6**: Performance optimization, edge case handling
- **Week 7-8**: Final polishing, v1.0.0 stable release preparation

**Success Criteria**:
- ✅ 10+ active beta testers
- ✅ No critical bugs outstanding
- ✅ 90%+ user satisfaction
- ✅ Complete documentation coverage

---

## Beta Tester Benefits

As a PopKit beta tester, you get:

1. **Early Access**: Try new features before public release
2. **Direct Input**: Shape the product roadmap
3. **Recognition**: Listed in CONTRIBUTORS.md (opt-in)
4. **Free Tier**: Lifetime access to core features
5. **Priority Support**: Fast response to issues

---

## Thank You!

Your participation in this beta is invaluable. Every bug report, feature request, and piece of feedback helps make PopKit better for the entire community.

Happy testing! 🚀

---

**Questions?** Open an issue: https://github.com/jrc1883/popkit/issues
**Updates**: Follow the project for release announcements
