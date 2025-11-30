---
name: Bug Report
about: Report something that isn't working correctly
title: "[Bug] "
labels: bug
assignees: ''
---

## Priority: [LOW/MEDIUM/HIGH/CRITICAL]

## Description

A clear description of what the bug is.

## Steps to Reproduce

1. Go to '...'
2. Run command '...'
3. See error

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened.

## Environment

- Claude Code version:
- OS:
- Shell:

## Component

Which part of popkit is affected?
- [ ] Skills (`pop:*`)
- [ ] Agents
- [ ] Commands (`/popkit:*`)
- [ ] Hooks
- [ ] Power Mode
- [ ] Other

## Error Messages

```
Paste any error messages here
```

---

## PopKit Guidance

<!-- This section helps Claude Code debug and fix this issue -->

### Debugging Workflow
- [ ] **Use Systematic Debugging** - Invoke `pop-systematic-debugging` skill
- [ ] **Root Cause Tracing** - Invoke `pop-root-cause-tracing` skill
- [ ] **Quick Fix** - Issue is straightforward, proceed directly

### Suggested Agents
- Primary: `bug-whisperer`
- Supporting: `test-writer-fixer`

### Investigation Areas
<!-- Where to look for the root cause -->
- [ ] Hook execution (`hooks/`)
- [ ] Agent routing (`agents/config.json`)
- [ ] Skill definition (`skills/`)
- [ ] Command logic (`commands/`)
- [ ] Power Mode coordination (`power-mode/`)

### Quality Gates
- [ ] Fix doesn't break existing tests
- [ ] Regression test added
- [ ] TypeScript check passes
- [ ] Related functionality verified

### Rollback Plan
<!-- If fix causes issues -->
- Affected files:
- Safe rollback: `git checkout <commit> -- <files>`

---

## Additional Context

Any other context about the problem:
