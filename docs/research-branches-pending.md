# Pending Research Branches from Claude Code Web

**Date Detected:** 2025-12-16
**Count:** 14 branches
**Source:** Claude Code Web sessions (browser-based research)

## What Are These?

When you use Claude Code in the browser (not CLI), it creates research branches like `claude/research-*` or `claude/investigate-*`. These branches contain findings, analysis, and documentation from web sessions.

## Detected Branches

| Branch | Likely Topic | Related Issue |
|--------|-------------|---------------|
| `build-popkit-readme-UfKd9` | Documentation website | #251 |
| `code-commenting-investigation-cTC4s` | Code standards | #252 |
| `investigate-batch-spawning-I2aUY` | Status messages | #253 |
| `research-vibe-engineering-a0J4y` | Market research | #249 |
| `keep-terminal-helper-text-zVY23` | Terminal enhancement | #248 |
| `analyze-slack-notification-GCaQZ` | Slack integration | - |
| `async-agent-orchestration-egT0Y` | Async orchestration | - |
| `explore-gist-integration-URSHW` | Gist integration | - |
| `analyze-popkit-startup-lr32y` | Startup analysis | - |
| `add-scratch-pad-feature-tTEcB` | Scratch pad feature | - |
| `pop-kit-script-execution-sOHL9` | Script execution | - |
| `research-cli-tools-Dg3ui` | CLI tools | - |
| `skill-structure-organization-01PzL9WuqrVfUnwReHMfa2eX` | Skill organization | - |

## How to Process

When ready to process these (future session):

1. **Use the skill:** Invoke `pop-research-merge` skill
2. **What it does:**
   - Analyzes research content in each branch
   - Organizes documentation in `docs/research/`
   - Creates GitHub issues for actionable items
   - Links branches to existing issues where applicable
3. **Time estimate:** 30-60 minutes depending on content volume

## Notes

- Some branches already have corresponding issues (#248, #249, #251, #252, #253)
- Others may contain new findings not yet tracked
- Processing can be done in batches (e.g., 3-5 branches at a time)
- No urgency - these are research findings, not blocking work

## When to Process

Good times to process research branches:
- Start of sprint planning
- When looking for new work items
- During project organization sessions
- When preparing roadmap updates

**Status:** Not urgent - document for future reference
**Next:** Run `/popkit:routine nightly` when ready
