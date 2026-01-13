---
name: Feature Request
about: Suggest a new feature or enhancement for popkit
title: "[Feature] Integrate Recent Claude Code Platform Updates (v2.0.60-v2.0.62)"
labels: enhancement
assignees: ""
---

## Priority: HIGH

## Summary

Integrate three high-value, low-overhead features from recent Claude Code platform updates (v2.0.60-v2.0.62) to improve PopKit's user experience and align with Anthropic's latest capabilities:

1. **Background Agent Support** - Enable long-running agents to run async
2. **Recommended Options** - Improve UX for AskUserQuestion prompts
3. **Customizable Attribution** - Make commit/PR bylines configurable per agent

## Use Case

### Background Agents

Currently, Power Mode and multi-agent workflows block the user during execution. With background agent support, users can:

- Run `/popkit:power --background` and continue coding
- Execute morning/nightly routines async
- Let feature-workflow exploration phase run while working on other tasks

### Recommended Options

PopKit heavily uses AskUserQuestion (per CLAUDE.md standards). Adding "recommended" hints improves decision-making:

- `/popkit:git finish` can highlight best-practice options
- Routine prompts can guide users toward better choices
- First-time users get implicit guidance without reading docs

### Customizable Attribution

Current hardcoded attribution doesn't reflect PopKit's multi-agent architecture:

```
Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

Should show which agent contributed:

```
Generated with PopKit + Claude Code
Co-Authored-By: PopKit Agent (bug-whisperer) <noreply@popkit.dev>
```

## Proposed Solution

### 1. Background Agent Support (~2 hours)

**Files to modify:**

- `packages/plugin/agents/config.json` - Add `background_enabled` per agent
- `packages/plugin/power-mode/coordinator.py` - Add `--background` flag handling
- `packages/plugin/commands/power.md` - Document `--background` flag

**Implementation:**

```python
# power-mode/coordinator.py
if args.background:
    # Use Claude Code's background agent API
    subprocess.Popen([...])  # Non-blocking
else:
    subprocess.run([...])    # Blocking (current behavior)
```

**Agents to enable:**

- `power-coordinator` (high effort)
- `code-explorer` (medium effort)
- `researcher` (medium effort)

### 2. Recommended Options (~1 hour)

**Files to modify:**

- All skills using AskUserQuestion (search for `AskUserQuestion` in `packages/plugin/skills/`)
- Key targets:
  - `packages/plugin/skills/pop-finish-branch/SKILL.md`
  - `packages/plugin/skills/pop-code-review/SKILL.md`
  - `packages/plugin/commands/routine.md`

**Pattern:**

```python
# Before
options = [
  {"label": "Merge", "description": "Merge to main"},
  {"label": "PR", "description": "Create pull request"}
]

# After
options = [
  {"label": "PR", "description": "Create pull request", "recommended": True},
  {"label": "Merge", "description": "Merge to main"}
]
```

**Heuristics for recommendations:**

- `/popkit:git finish` → Recommend "Create PR" over direct merge
- `/popkit:routine run` → Recommend saving successful routines
- Power Mode → Recommend Redis mode if Docker available

### 3. Attribution Settings (~1 hour)

**Files to modify:**

- `packages/plugin/.claude-plugin/plugin.json` - Add attribution config
- `packages/plugin/commands/git.md:68-76` - Use dynamic attribution
- Template: `packages/plugin/output-styles/pr-description.md`

**Config schema:**

```json
{
  "attribution": {
    "style": "popkit", // "popkit", "claude", "custom", "none"
    "commit_suffix": "Generated with PopKit + Claude Code\n\nCo-Authored-By: PopKit Agent ({agent}) <noreply@popkit.dev>",
    "pr_footer": "---\n🤖 Generated with PopKit + Claude Code",
    "include_agent_name": true,
    "include_model_name": true // New in v2.0.62
  }
}
```

**Dynamic replacement:**

- `{agent}` → agent name from context
- `{model}` → sonnet/opus/haiku
- `{timestamp}` → ISO 8601

## Alternatives Considered

### GitHub Actions Integration

We reviewed `anthropics/claude-code-action` for potential integration but determined:

- ❌ Too much overhead (separate package, marketplace publishing)
- ❌ PopKit already has strong git/CI integration
- ✅ Better as future consideration after core features stabilize

### MCP Server Toggling

CHANGELOG v2.0.60 added `/mcp enable/disable` commands. Considered adding `/popkit:mcp` command but:

- ❌ Lower priority than the three core features above
- ✅ Good candidate for v0.9.11 or v0.10.0

## Component

Which part of popkit does this relate to?

- [ ] Skills (`pop:*`)
- [x] Agents (tier-1, tier-2, feature-workflow)
- [x] Commands (`/popkit:*`)
- [ ] Hooks
- [ ] Output Styles
- [x] Power Mode
- [ ] MCP Server Template
- [x] Documentation
- [ ] Other

## Acceptance Criteria

### Background Agents

- [x] `config.json` includes `background_enabled` flag per agent
- [x] Power Mode coordinator supports `--background` flag
- [x] Documentation updated in `commands/power.md`
- [x] Works for code-explorer, researcher, power-coordinator agents
- [x] Fallback to blocking mode if background not supported

### Recommended Options

- [x] At least 5 skills updated with `recommended: true` hints
- [x] `/popkit:git finish` highlights "Create PR" as recommended
- [x] `/popkit:routine run` recommends saving successful routines
- [x] Power Mode setup recommends Redis if Docker detected
- [x] Documentation updated in CLAUDE.md User Interaction Standard section

### Attribution Settings

- [x] `plugin.json` includes attribution configuration schema
- [x] Git commit command uses dynamic attribution
- [x] Agent name appears in Co-Authored-By when available
- [x] Backward compatible (defaults to current behavior)
- [x] Documentation updated with configuration examples

### General

- [x] No breaking changes to existing commands/skills
- [x] All three features independently toggleable
- [x] Version bumped to 0.9.11
- [x] CHANGELOG.md updated with new features

## Related Issues

_Research based on:_

- [anthropics/claude-code CHANGELOG v2.0.60-v2.0.62](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action)

---

## PopKit Guidance

<!-- This section helps Claude Code work on this issue effectively -->

### Workflow

- [ ] **Brainstorm First** - Use `pop-brainstorming` skill before implementation
- [x] **Plan Required** - Use `/popkit:write-plan` to create implementation plan
- [ ] **Direct Implementation** - Can proceed directly to code

### Development Phases

<!-- Check which phases apply to this feature -->

- [x] Discovery - Research and context gathering ✅ COMPLETED
- [x] Architecture - Design decisions needed
- [x] Implementation - Code changes
- [ ] Testing - Test coverage required
- [x] Documentation - Docs updates needed
- [ ] Review - Code review checkpoint

### Suggested Agents

<!-- Agents that should be involved -->

- Primary: `refactoring-expert`
- Supporting: `documentation-maintainer`, `code-reviewer`

### Quality Gates

<!-- Validation required between phases -->

- [ ] TypeScript check (`tsc --noEmit`) - N/A (config-only changes)
- [ ] Build verification - N/A (no build step)
- [ ] Lint pass
- [ ] Test pass - Run `/popkit:plugin-test` after changes
- [x] Manual review checkpoint

### Power Mode

- [ ] **Recommended** - Multiple agents should work in parallel
- [x] **Optional** - Can benefit from coordination
- [ ] **Not Needed** - Sequential work is fine

### Estimated Complexity

- [ ] Small (1-2 files, < 100 lines)
- [x] Medium (3-5 files, 100-500 lines)
- [ ] Large (6+ files, 500+ lines)
- [ ] Epic (multiple PRs, architectural changes)

**Estimated Total Effort:** ~4 hours (all three features)

---

## Additional Context

### Source Analysis

#### CHANGELOG v2.0.62

- Added "(Recommended)" indicators for multiple-choice questions
- Introduced `attribution` setting to customize commit and PR bylines
- Fixed duplicate slash commands in symlinked configs
- Resolved skill file symlink circular reference issues

#### CHANGELOG v2.0.61

- Reverted VSCode multiple terminal client support (responsiveness concerns)

#### CHANGELOG v2.0.60

- **Background agent support** - agents run while you work
- Added `--disable-slash-commands` CLI flag
- Model names in "Co-Authored-By" commit messages
- MCP server toggling via `/mcp enable/disable`
- VSCode multiple terminal client support

### Implementation Priority Order

1. **Attribution settings** (1 hour) - Quick config change, immediate branding benefit
2. **Recommended options** (1 hour) - Improves UX across all commands
3. **Background agents** (2 hours) - Enables better Power Mode UX

**Total:** ~4 hours for all three features

### Future Considerations (Post v0.9.11)

- **MCP Toggling Command** (`/popkit:mcp enable/disable`) - v0.9.12 candidate
- **PopKit GitHub Action** - Separate package for automated PR reviews using popkit agents
- **Model Name in Attribution** - Already supported in v2.0.62, just needs config exposure

### Files Modified (Expected)

```
packages/plugin/
  .claude-plugin/
    plugin.json                          # Attribution config
  agents/
    config.json                          # Background agent flags
  commands/
    git.md                               # Dynamic attribution usage
    power.md                             # Background flag docs
  power-mode/
    coordinator.py                       # Background execution
  skills/
    pop-finish-branch/SKILL.md           # Recommended options
    pop-code-review/SKILL.md             # Recommended options
    pop-systematic-debugging/SKILL.md    # Recommended options
  output-styles/
    pr-description.md                    # Attribution template
CLAUDE.md                                # Documentation updates
CHANGELOG.md                             # Version 0.9.11 entry
```

### Testing Plan

1. **Manual Testing**
   - Run `/popkit:power --background` and verify non-blocking
   - Trigger `/popkit:git finish` and verify "Create PR" is marked recommended
   - Create commit and verify agent name appears in Co-Authored-By

2. **Automated Testing**
   - Run `/popkit:plugin-test` to validate plugin integrity
   - Verify no regressions in existing workflows

3. **Edge Cases**
   - Background flag on non-background-capable agents (should fallback)
   - Attribution with no agent context (should use default)
   - Recommended option when user selects non-recommended (should still work)
