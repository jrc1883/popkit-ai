# PopKit

<div align="center">

**Development workflows that actually work**

Start each day knowing your project is healthy.
End each day with context saved for tomorrow.
Know exactly what to do next.

[Get Started](#get-started) · [Morning Routine](#morning-routine) · [What's Next](#whats-next) · [Docs](https://popkit.unjoe.me)

</div>

---

## What is PopKit?

PopKit organizes your Claude Code sessions around **workflows, not tools**.

Most AI coding assistants give you a prompt and say "figure it out." PopKit gives you:

- **[Morning routines](https://popkit.unjoe.me/features/routines/)** that check your project health before you write code
- **["What's next?"](https://popkit.unjoe.me/reference/commands/#popkit-devnext)** recommendations based on your actual git status, failing tests, and open issues
- **[Guided development](https://popkit.unjoe.me/features/feature-dev/)** that walks you through feature implementation phase by phase
- **[Session capture](https://popkit.unjoe.me/features/routines/#nightly-routine)** so you can pick up exactly where you left off

It's the difference between "here's an AI" and "here's how to use AI to build software."

---

## Command Tiers

PopKit intentionally exposes two layers:

| Layer             | Prefix     | Purpose                                                      | Default  |
| ----------------- | ---------- | ------------------------------------------------------------ | -------- |
| Workflow commands | `/popkit-` | User-facing orchestration across commands, skills, and hooks | Yes      |
| Direct skills     | `/pop-`    | Low-level primitives for targeted/advanced invocation        | Advanced |

Example: `/popkit-dev:next` uses `pop-next-action` internally, then adds [mode handling, reporting, and command-level guidance](https://popkit.unjoe.me/concepts/commands/#what-commands-add).

---

## Get Started

### Claude Code Plugin (recommended)

```bash
# Add the PopKit marketplace
/plugin marketplace add jrc1883/popkit-ai

# Install the plugins you need
/plugin install popkit-core@popkit-ai   # Foundation
/plugin install popkit-dev@popkit-ai    # Development workflows

# Restart Claude Code, then run your first morning routine:
/popkit-dev:routine morning
```

### VS Code / Copilot (one-click install)

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=popkit&config=%7B%22command%22%3A%20%22popkit-mcp%22%2C%20%22args%22%3A%20%5B%22--transport%22%2C%20%22stdio%22%5D%7D) [![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=popkit&config=%7B%22command%22%3A%20%22popkit-mcp%22%2C%20%22args%22%3A%20%5B%22--transport%22%2C%20%22stdio%22%5D%7D&quality=insiders)

Requires `pip install popkit-mcp` first, then click the badge above.

### PyPI (for MCP server or standalone use)

```bash
# MCP server only — for Cursor, Codex CLI, Copilot, or any MCP client
pip install popkit-mcp
popkit-mcp --transport stdio

# Full install — CLI + shared utilities + MCP server
pip install popkit[full]

# Or install individual packages
pip install popkit-shared   # Core utilities only
pip install popkit-cli      # CLI only
pip install popkit[mcp]     # Core + CLI + MCP server
```

---

## Morning Routine

Every morning, PopKit checks your project's vital signs:

```
/popkit-dev:routine morning
```

```
■ Session Restored
  Last: Fixed authentication flow (2h ago)

■ Ready to Code Score: 87/100

  ✓ Git status clean
  ✓ Tests passing (142/142)
  ✓ CI green on main
  ⚠ 2 dependencies outdated
  ✓ No TypeScript errors

■ Context Loaded
  Active issue: #47 Add password reset flow
  Branch: feat/password-reset (3 commits ahead of main)

Ready to continue.
```

The ["Ready to Code" score](https://popkit.unjoe.me/features/routines/#morning-routine) tells you if something needs attention before you start coding. 87 means you're good to go. 45 means something's broken.

---

## What's Next

When you're not sure what to work on:

```
/popkit-dev:next
```

PopKit analyzes your git status, test results, GitHub issues, and TypeScript errors to recommend prioritized actions:

```
Recommended Actions:

1. Merge main into branch (Score: 85)
   Branch is 5 commits behind main

2. Fix TypeScript error in src/auth.ts:47 (Score: 78)
   Type 'string | undefined' is not assignable to type 'string'

3. Continue issue #47 (Score: 72)
   Password reset flow - implementation started

4. Review PR #51 (Score: 65)
   Dependency update, waiting 2 days
```

No more staring at your terminal wondering what to do.

---

## Guided Development

Start a feature with [`/popkit-dev:dev`](https://popkit.unjoe.me/features/feature-dev/):

```
/popkit-dev:dev "Add password reset via email"
```

PopKit walks you through [seven phases](https://popkit.unjoe.me/features/feature-dev/#the-7-phases):

1. **Discovery** — What exactly are we building?
2. **Exploration** — What patterns exist in this codebase?
3. **Questions** — What do we need to clarify before coding?
4. **Architecture** — How should we structure this?
5. **Implementation** — Write the code, phase by phase
6. **Review** — Check what we built
7. **Summary** — Document what changed

Each phase has checkpoints. You approve before moving forward.

---

## Nightly Routine

End your day with context saved:

```
/popkit-dev:routine nightly
```

```
■ [Sleep Score](https://popkit.unjoe.me/features/routines/#nightly-routine): 92/100

  ✓ All changes committed
  ✓ Branch pushed to origin
  ✓ Tests passing
  ✓ No uncommitted stashes
  ✓ Session branches clean

■ Session Captured
  Work: Implemented password reset email flow
  Next: Add reset token validation endpoint

■ Dependencies
  2 security updates available (non-breaking)

Sweet dreams.
```

Tomorrow's morning routine will restore this context automatically.

---

## The Philosophy

PopKit tries to be **programmatic where possible, AI where needed**.

| Approach                  | What it means                                       |
| ------------------------- | --------------------------------------------------- |
| **Programmatic git**      | Status checks are scripts, not AI guesses           |
| **Rule-based validation** | TypeScript errors come from `tsc`, not prompts      |
| **Explicit state**        | Session context is JSON, not memory                 |
| **AI for judgment**       | Architecture decisions, code review, prioritization |

This reduces token usage, makes workflows reproducible, and keeps AI focused on what it's actually good at.

---

## Parallel Development

Work on multiple features simultaneously with [worktree management](https://popkit.unjoe.me/reference/commands/#popkit-devworktree):

```
/popkit-dev:worktree list
```

PopKit adds batch operations and health analysis on top of git worktrees:

- **`update-all`** — Pull latest changes across all worktrees at once
- **`analyze`** — Get recommendations for stale worktrees, uncommitted changes
- **`init`** — Auto-create worktrees from branch patterns

No more manual worktree juggling when you're working on multiple features.

---

## More Plugins

PopKit is modular. Install what you need:

| Plugin              | What it adds                                                                                                                           |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **popkit-core**     | Project setup, [Power Mode](https://popkit.unjoe.me/features/power-mode/) (multi-agent), session management                            |
| **popkit-dev**      | Git workflows, worktrees, [routines](https://popkit.unjoe.me/features/routines/), `/next` recommendations                              |
| **popkit-ops**      | Quality assessments, security scanning, debugging, [deployment pipeline](https://popkit.unjoe.me/reference/commands/#popkit-opsdeploy) |
| **popkit-research** | Knowledge capture, research notes, documentation sync                                                                                  |

```bash
/plugin install popkit-ops@popkit-ai      # Quality & security
/plugin install popkit-research@popkit-ai # Knowledge management
```

---

## Requirements

- Claude Code 2.1.33+ (tested through 2.1.80)
- Python 3.11+
- Git
- GitHub CLI (`gh`) for GitHub integration

---

## Documentation

- **[Documentation Site](https://popkit.unjoe.me)** — Guides and references
- **[CHANGELOG.md](CHANGELOG.md)** — Version history
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — How to contribute

---

## Status

**Version:** 1.0.0-beta.13
**Status:** Public beta — core features stable, actively improving

---

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0) — see [LICENSE](LICENSE)

This software is free for personal, educational, and noncommercial use.

---

<div align="center">

**[Back to Top](#popkit)**

</div>
