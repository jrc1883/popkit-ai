## Description

<!-- Provide a clear, concise summary of your changes -->

## Type of Change

<!-- Check all that apply -->
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Refactoring (code improvement without changing functionality)
- [ ] Performance improvement
- [ ] Test addition/update
- [ ] CI/CD changes
- [ ] Dependency update

## Related Issues

<!-- Link to related issues using keywords -->
<!-- Examples: Closes #123, Fixes #456, Relates to #789 -->

## Changes Made

<!-- Provide a bullet list of specific changes -->
-
-
-

## Plugin Impact

<!-- Which plugins are affected by this change? -->
- [ ] popkit-core
- [ ] popkit-dev
- [ ] popkit-ops
- [ ] popkit-research
- [ ] shared-py
- [ ] cloud (private)
- [ ] None (documentation/CI only)

## Testing Performed

<!-- Describe how you tested your changes -->

### Manual Testing
<!-- What manual testing did you perform? -->
- [ ] Tested locally with `/plugin install ./packages/<plugin-name>`
- [ ] Verified in Claude Code (version: ______)
- [ ] Tested affected commands/skills/agents

### Automated Testing
<!-- What automated tests did you run? -->
- [ ] Plugin tests passed (`python run_all_tests.py`)
- [ ] Specific test category: ____________

### Test Results
```
<!-- Paste relevant test output or results here -->

```

## Screenshots

<!-- If your changes include UI/output changes, add screenshots here -->
<!-- Delete this section if not applicable -->

## Checklist

<!-- Review this checklist before submitting your PR -->

### Code Quality
- [ ] Code follows existing patterns and conventions
- [ ] No hardcoded secrets or sensitive data
- [ ] Paths use forward slashes and `${CLAUDE_PLUGIN_ROOT}` where applicable
- [ ] Python hooks follow JSON stdin/stdout protocol
- [ ] Conventional commit format used (feat:, fix:, docs:, etc.)

### Testing & Validation
- [ ] Plugin tests pass (`python run_all_tests.py`)
- [ ] CI checks pass (plugin validation, agents, hooks)
- [ ] No IP leaks detected (IP scanner check)
- [ ] Manual testing completed
- [ ] Tests added/updated for new functionality (if applicable)

### Documentation
- [ ] Documentation updated (README, CLAUDE.md, etc.)
- [ ] CHANGELOG.md updated with version and changes
- [ ] Comments added for complex logic
- [ ] Plugin manifest updated (if adding commands/skills/agents)

### Breaking Changes
- [ ] No breaking changes introduced
- [ ] OR: Breaking changes are documented below

<!-- If breaking changes exist, describe them here and provide migration guide -->

### Plugin-Specific (if applicable)
- [ ] Command YAML frontmatter is valid
- [ ] Skill SKILL.md format follows standards
- [ ] Agent AGENT.md includes purpose, triggers, capabilities
- [ ] Hook execution tested (timeout, error handling)

## Additional Context

<!-- Any additional context, design decisions, or notes for reviewers -->

---

## For Reviewers

<!-- This section helps reviewers understand the scope and focus areas -->

### Review Focus Areas
<!-- What should reviewers pay special attention to? -->
-
-

### Testing Instructions
<!-- How can reviewers test these changes? -->
1.
2.
3.

### Known Limitations
<!-- Are there any known limitations or follow-up work needed? -->
-

---

**Note for Contributors:**
- This repository uses the IP Leak Scanner to protect proprietary content. Ensure no sensitive data is included.
- All plugins are configuration-only (no build/compile steps needed).
- Test locally before submitting: `/plugin install ./packages/<plugin-name>`
- See [CLAUDE.md](CLAUDE.md) for full contribution guidelines.
