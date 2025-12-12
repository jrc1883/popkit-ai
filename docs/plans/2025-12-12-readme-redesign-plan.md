# README Redesign Implementation Plan

> **For Claude:** Use executing-plans skill to implement this plan task-by-task.

**Goal:** Redesign PopKit's README with bubblegum aesthetic, before/after hook, and auto-generated sections.

**Architecture:** Create asset infrastructure (directories, VHS tapes), build auto-gen sync script, then rewrite README using new structure. Visual assets require VHS tool for terminal GIFs.

**Tech Stack:** Python (sync script), VHS (terminal recordings), Markdown, GitHub Actions

---

## Task 1: Create Asset Directory Structure

**Files:**
- Create: `packages/plugin/assets/`
- Create: `packages/plugin/assets/tapes/`
- Create: `packages/plugin/assets/images/`
- Create: `packages/plugin/scripts/`

**Step 1: Create directories**

```bash
mkdir -p packages/plugin/assets/tapes
mkdir -p packages/plugin/assets/images
mkdir -p packages/plugin/scripts
```

**Step 2: Verify structure**

Run: `ls -la packages/plugin/assets/ && ls -la packages/plugin/scripts/`
Expected: Empty directories exist

**Step 3: Create .gitkeep files**

```bash
touch packages/plugin/assets/tapes/.gitkeep
touch packages/plugin/assets/images/.gitkeep
```

**Step 4: Commit**

```bash
git add packages/plugin/assets packages/plugin/scripts
git commit -m "chore: create asset directories for README redesign (#184)"
```

---

## Task 2: Create VHS Tape File - Morning Routine Demo

**Files:**
- Create: `packages/plugin/assets/tapes/morning-routine.tape`

**Step 1: Create the tape file**

```tape
# Morning Routine Demo
# Shows /popkit:routine morning in action

Output assets/images/morning-routine.gif

Set FontSize 14
Set Width 800
Set Height 500
Set Theme "Catppuccin Mocha"
Set Padding 20

Type "/popkit:routine morning"
Sleep 500ms
Enter
Sleep 3s

# Simulate output appearing
Type@50ms "┌──────────────────────────────────────┐"
Enter
Type@50ms "│  MORNING ROUTINE - Ready to Code     │"
Enter
Type@50ms "├──────────────────────────────────────┤"
Enter
Type@50ms "│  Git Status:     ✓ Clean             │"
Enter
Type@50ms "│  TypeScript:     ✓ No errors         │"
Enter
Type@50ms "│  Dependencies:   ✓ Up to date        │"
Enter
Type@50ms "├──────────────────────────────────────┤"
Enter
Type@50ms "│  Ready to Code Score: 95/100         │"
Enter
Type@50ms "└──────────────────────────────────────┘"
Enter

Sleep 2s
```

**Step 2: Verify tape file syntax**

Run: `cat packages/plugin/assets/tapes/morning-routine.tape | head -10`
Expected: Tape file content visible

**Step 3: Commit**

```bash
git add packages/plugin/assets/tapes/morning-routine.tape
git commit -m "feat(assets): add morning routine VHS tape file (#184)"
```

---

## Task 3: Create VHS Tape File - Before/After Hero

**Files:**
- Create: `packages/plugin/assets/tapes/before-after.tape`

**Step 1: Create the tape file**

```tape
# Before/After Hero Demo
# Shows the transformation PopKit provides

Output assets/images/before-after.gif

Set FontSize 14
Set Width 900
Set Height 600
Set Theme "Catppuccin Mocha"
Set Padding 20

# "Without PopKit" section
Type "# Without PopKit..."
Enter
Sleep 1s

Type "git status"
Enter
Sleep 500ms
Type "npm run typecheck"
Enter
Sleep 500ms
Type "npm run lint"
Enter
Sleep 500ms
Type "gh issue view 57"
Enter
Sleep 500ms
Type "# Manually check each thing..."
Enter
Sleep 1s

# Clear and show "With PopKit"
Ctrl+L
Sleep 500ms

Type "# With PopKit..."
Enter
Sleep 1s

Type "/popkit:dev work #57"
Enter
Sleep 2s

Type@30ms "✓ Fetched issue #57: Add user authentication"
Enter
Type@30ms "✓ Created worktree: .worktrees/issue-57"
Enter
Type@30ms "✓ Health check: Ready to Code (95/100)"
Enter
Type@30ms "✓ Starting Phase 1: Discovery..."
Enter
Sleep 2s
```

**Step 2: Verify tape file**

Run: `wc -l packages/plugin/assets/tapes/before-after.tape`
Expected: ~40 lines

**Step 3: Commit**

```bash
git add packages/plugin/assets/tapes/before-after.tape
git commit -m "feat(assets): add before/after hero VHS tape file (#184)"
```

---

## Task 4: Create Auto-Gen Sync Script

**Files:**
- Create: `packages/plugin/scripts/sync-readme.py`

**Step 1: Write the sync script**

```python
#!/usr/bin/env python3
"""
README Auto-Generation Sync Script

Scans commands and agents directories, extracts metadata,
and updates AUTO-GEN sections in README.md.

Usage:
    python scripts/sync-readme.py [--dry-run]
"""

import os
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional


def extract_frontmatter(file_path: Path) -> Optional[Dict]:
    """Extract YAML frontmatter from markdown file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return yaml.safe_load(parts[1])
    except Exception:
        pass
    return None


def get_commands(commands_dir: Path) -> List[Dict]:
    """Scan commands directory and extract metadata."""
    commands = []
    for cmd_file in sorted(commands_dir.glob('*.md')):
        if cmd_file.name.startswith('_'):
            continue

        meta = extract_frontmatter(cmd_file)
        if not meta:
            # Try to extract from content
            content = cmd_file.read_text(encoding='utf-8')
            name = cmd_file.stem
            # Look for description in first paragraph
            lines = content.split('\n')
            desc = ''
            for line in lines:
                if line.strip() and not line.startswith('#') and not line.startswith('-'):
                    desc = line.strip()[:80]
                    break
            commands.append({'name': name, 'description': desc})
        else:
            commands.append({
                'name': meta.get('name', cmd_file.stem),
                'description': meta.get('description', '')[:80]
            })
    return commands


def get_agents(agents_dir: Path) -> Dict[str, List[Dict]]:
    """Scan agents directory and extract metadata by tier."""
    tiers = {
        'tier-1-always-active': [],
        'tier-2-on-demand': [],
        'feature-workflow': []
    }

    for tier_name in tiers.keys():
        tier_dir = agents_dir / tier_name
        if not tier_dir.exists():
            continue

        for agent_dir in sorted(tier_dir.iterdir()):
            if not agent_dir.is_dir() or agent_dir.name.startswith('_'):
                continue

            agent_file = agent_dir / 'AGENT.md'
            if not agent_file.exists():
                continue

            meta = extract_frontmatter(agent_file)
            if meta:
                tiers[tier_name].append({
                    'name': meta.get('name', agent_dir.name),
                    'description': meta.get('description', '')[:60]
                })
            else:
                # Extract from content
                content = agent_file.read_text(encoding='utf-8')
                name = agent_dir.name
                desc = ''
                for line in content.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        desc = line.strip()[:60]
                        break
                tiers[tier_name].append({'name': name, 'description': desc})

    return tiers


def generate_commands_table(commands: List[Dict]) -> str:
    """Generate markdown table for commands."""
    lines = [
        "| Command | Description |",
        "|---------|-------------|"
    ]
    for cmd in commands:
        lines.append(f"| `/popkit:{cmd['name']}` | {cmd['description']} |")
    return '\n'.join(lines)


def generate_agents_section(tiers: Dict[str, List[Dict]]) -> str:
    """Generate markdown for agents by tier."""
    tier_names = {
        'tier-1-always-active': 'Tier 1: Always Active',
        'tier-2-on-demand': 'Tier 2: On-Demand',
        'feature-workflow': 'Feature Workflow'
    }

    lines = []
    for tier_key, tier_label in tier_names.items():
        agents = tiers.get(tier_key, [])
        if not agents:
            continue

        lines.append(f"### {tier_label} ({len(agents)} agents)")
        lines.append("")
        lines.append("| Agent | Purpose |")
        lines.append("|-------|---------|")
        for agent in agents:
            lines.append(f"| **{agent['name']}** | {agent['description']} |")
        lines.append("")

    return '\n'.join(lines)


def update_readme(readme_path: Path, section_name: str, content: str, dry_run: bool = False) -> bool:
    """Update a specific AUTO-GEN section in README."""
    start_marker = f"<!-- AUTO-GEN:{section_name} START -->"
    end_marker = f"<!-- AUTO-GEN:{section_name} END -->"

    readme_content = readme_path.read_text(encoding='utf-8')

    pattern = re.compile(
        rf'{re.escape(start_marker)}.*?{re.escape(end_marker)}',
        re.DOTALL
    )

    replacement = f"{start_marker}\n{content}\n{end_marker}"

    if pattern.search(readme_content):
        new_content = pattern.sub(replacement, readme_content)
        if not dry_run:
            readme_path.write_text(new_content, encoding='utf-8')
        return True
    else:
        print(f"Warning: Markers for {section_name} not found in README", file=sys.stderr)
        return False


def main():
    dry_run = '--dry-run' in sys.argv

    # Find paths
    script_dir = Path(__file__).parent
    plugin_dir = script_dir.parent
    readme_path = plugin_dir / 'README.md'
    commands_dir = plugin_dir / 'commands'
    agents_dir = plugin_dir / 'agents'

    if not readme_path.exists():
        print(f"Error: README not found at {readme_path}", file=sys.stderr)
        sys.exit(1)

    print(f"{'[DRY RUN] ' if dry_run else ''}Syncing README...")

    # Generate commands section
    if commands_dir.exists():
        commands = get_commands(commands_dir)
        commands_table = generate_commands_table(commands)
        if update_readme(readme_path, 'COMMANDS', commands_table, dry_run):
            print(f"  ✓ Updated COMMANDS ({len(commands)} commands)")

    # Generate agents section
    if agents_dir.exists():
        tiers = get_agents(agents_dir)
        agents_content = generate_agents_section(tiers)
        total_agents = sum(len(agents) for agents in tiers.values())
        if update_readme(readme_path, 'AGENTS', agents_content, dry_run):
            print(f"  ✓ Updated AGENTS ({total_agents} agents)")

    print("Done!")


if __name__ == '__main__':
    main()
```

**Step 2: Make script executable**

```bash
chmod +x packages/plugin/scripts/sync-readme.py
```

**Step 3: Test the script (dry run)**

Run: `cd packages/plugin && python scripts/sync-readme.py --dry-run`
Expected: Output showing what would be updated (will warn about missing markers)

**Step 4: Commit**

```bash
git add packages/plugin/scripts/sync-readme.py
git commit -m "feat(scripts): add README auto-gen sync script (#184)"
```

---

## Task 5: Rewrite README - Structure and Banner

**Files:**
- Modify: `packages/plugin/README.md`

**Step 1: Create new README with structure**

```markdown
<p align="center">
  <img src="https://raw.githubusercontent.com/jrc1883/popkit-claude/main/assets/images/popkit-banner.png" alt="PopKit" width="600">
</p>

<p align="center">
  <strong>AI-powered workflows for Claude Code</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Claude%20Code-Plugin-purple?style=flat-square" alt="Claude Code Plugin">
</p>

---

## See the Difference

<p align="center">
  <img src="https://raw.githubusercontent.com/jrc1883/popkit-claude/main/assets/images/before-after.gif" alt="Before and After PopKit" width="700">
</p>

---

## Quick Start

```bash
# Add the marketplace
/plugin marketplace add jrc1883/popkit-claude

# Install the plugin
/plugin install popkit@popkit-claude
```

**Restart Claude Code** to activate. Then try:

```bash
/popkit:routine morning    # Start with a health check
/popkit:dev work #57       # Work on an issue end-to-end
/popkit:git commit         # Smart commit with auto-message
```

---

## What is PopKit?

PopKit orchestrates Claude Code's full power for real-world development workflows.

Claude Code has 20+ tools. But chaining them into coherent workflows? That's where PopKit comes in. It turns individual commands into orchestrated development pipelines—from morning health checks to complete feature implementations.

**Think of it as:** The difference between having ingredients and having a recipe.

---

## Features

### Development Workflows

Go from idea to implementation with guided 7-phase development:

<p align="center">
  <img src="https://raw.githubusercontent.com/jrc1883/popkit-claude/main/assets/images/dev-workflow.gif" alt="Development Workflow" width="700">
</p>

```bash
/popkit:dev "user authentication"  # Full guided workflow
/popkit:dev work #57               # Issue-driven development
/popkit:dev brainstorm "feature"   # Idea refinement
```

### Morning & Nightly Routines

Start and end your day with health checks:

<p align="center">
  <img src="https://raw.githubusercontent.com/jrc1883/popkit-claude/main/assets/images/morning-routine.gif" alt="Morning Routine" width="700">
</p>

```bash
/popkit:routine morning    # Ready to Code score (0-100)
/popkit:routine nightly    # Sleep Score (0-100)
```

### Power Mode

Multiple agents collaborating in parallel:

<p align="center">
  <img src="https://raw.githubusercontent.com/jrc1883/popkit-claude/main/assets/images/power-mode.gif" alt="Power Mode" width="700">
</p>

```bash
/popkit:power init     # First-time setup
/popkit:power start    # Begin multi-agent session
```

---

## Commands

<details>
<summary><strong>View all commands</strong></summary>

<!-- AUTO-GEN:COMMANDS START -->
| Command | Description |
|---------|-------------|
| `/popkit:dev` | Development workflows - brainstorm, plan, execute |
| `/popkit:git` | Smart git operations with auto-generated messages |
| `/popkit:routine` | Morning health checks and nightly cleanup |
| `/popkit:project` | Project analysis and setup |
| `/popkit:issue` | GitHub issue management |
| `/popkit:power` | Multi-agent orchestration |
<!-- AUTO-GEN:COMMANDS END -->

</details>

---

## Agents

PopKit includes 30+ specialized agents organized by tier:

<details>
<summary><strong>View all agents</strong></summary>

<!-- AUTO-GEN:AGENTS START -->
### Tier 1: Always Active (11 agents)

| Agent | Purpose |
|-------|---------|
| **bug-whisperer** | Debug complex issues |
| **code-reviewer** | Quality review |
| **security-auditor** | Security analysis |
| **test-writer-fixer** | Test implementation |

### Tier 2: On-Demand (17 agents)

| Agent | Purpose |
|-------|---------|
| **ai-engineer** | ML/AI tasks |
| **devops-automator** | CI/CD automation |
| **rapid-prototyper** | Quick prototypes |
<!-- AUTO-GEN:AGENTS END -->

</details>

---

## FAQ

<details>
<summary><strong>How do I get started?</strong></summary>

Install the plugin, restart Claude Code, then run `/popkit:routine morning` to see your project health.
</details>

<details>
<summary><strong>What's the difference between /popkit:dev and just coding?</strong></summary>

`/popkit:dev` provides a structured 7-phase workflow with architecture design, code review, and quality gates. It's especially useful for larger features.
</details>

<details>
<summary><strong>Do I need Power Mode?</strong></summary>

Power Mode enables multiple agents working in parallel. For most tasks, sequential mode works fine. Power Mode shines for complex refactoring or large features.
</details>

<details>
<summary><strong>Can I use PopKit offline?</strong></summary>

Yes! The core plugin works entirely locally. Cloud features (pattern sharing, team sync) require a subscription.
</details>

---

## Premium

Some features require a PopKit subscription:

| Feature | Free | Pro ($9/mo) |
|---------|------|-------------|
| Core commands | ✓ | ✓ |
| Basic agents | ✓ | ✓ |
| Custom MCP server | - | ✓ |
| Power Mode (Redis) | - | ✓ |
| Pattern sharing | - | ✓ |

Upgrade with `/popkit:upgrade`

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 - see [LICENSE](LICENSE)

---

<p align="center">
  Built for the Claude Code community
  <br>
  <a href="https://github.com/jrc1883/popkit-claude/issues">Report Bug</a> •
  <a href="https://github.com/jrc1883/popkit-claude/issues">Request Feature</a>
</p>
```

**Step 2: Verify README renders correctly**

Run: `wc -l packages/plugin/README.md`
Expected: ~180-220 lines

**Step 3: Commit**

```bash
git add packages/plugin/README.md
git commit -m "feat(readme): redesign with bubblegum aesthetic (#184)

- Before/after hero hook
- What is PopKit? narrative section
- AUTO-GEN markers for commands and agents
- Collapsible sections for depth
- Visual placeholders for demo GIFs"
```

---

## Task 6: Run Sync Script to Populate Auto-Gen Sections

**Files:**
- Modify: `packages/plugin/README.md` (auto-gen sections)

**Step 1: Run the sync script**

Run: `cd packages/plugin && python scripts/sync-readme.py`
Expected:
```
Syncing README...
  ✓ Updated COMMANDS (N commands)
  ✓ Updated AGENTS (N agents)
Done!
```

**Step 2: Verify changes**

Run: `git diff packages/plugin/README.md | head -50`
Expected: Changes in AUTO-GEN sections

**Step 3: Commit**

```bash
git add packages/plugin/README.md
git commit -m "chore: sync auto-gen README sections (#184)"
```

---

## Task 7: Create GitHub Actions Workflow for Sync

**Files:**
- Create: `.github/workflows/sync-readme.yml`

**Step 1: Create the workflow file**

```yaml
# README Auto-Sync
#
# Automatically updates auto-generated README sections when
# commands or agents change.
#
# Part of Issue #184 (Documentation & README Overhaul)

name: Sync README

on:
  push:
    branches: [master, main]
    paths:
      - 'packages/plugin/commands/**'
      - 'packages/plugin/agents/**'
      - 'packages/plugin/scripts/sync-readme.py'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  sync:
    name: Update README Auto-Gen Sections
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Run sync script
        run: |
          cd packages/plugin
          python scripts/sync-readme.py

      - name: Check for changes
        id: check
        run: |
          if git diff --quiet packages/plugin/README.md; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Commit changes
        if: steps.check.outputs.changed == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add packages/plugin/README.md
          git commit -m "chore(readme): auto-sync generated sections [skip ci]"
          git push
```

**Step 2: Verify workflow syntax**

Run: `cat .github/workflows/sync-readme.yml | head -20`
Expected: Valid YAML

**Step 3: Commit**

```bash
git add .github/workflows/sync-readme.yml
git commit -m "ci: add README auto-sync workflow (#184)"
```

---

## Task 8: Create Placeholder Images

**Files:**
- Create: `packages/plugin/assets/images/popkit-banner.png` (placeholder)
- Create: `packages/plugin/assets/images/README-ASSETS.md`

**Step 1: Create assets documentation**

```markdown
# PopKit Visual Assets

This directory contains visual assets for the README and documentation.

## Current Assets

| Asset | Status | Description |
|-------|--------|-------------|
| `popkit-banner.png` | Placeholder | Main banner with bubblegum aesthetic |
| `before-after.gif` | Pending | Hero GIF showing workflow transformation |
| `morning-routine.gif` | Pending | Demo of morning routine |
| `power-mode.gif` | Pending | Demo of multi-agent collaboration |
| `dev-workflow.gif` | Pending | Demo of development workflow |

## Generating GIFs

GIFs are generated from VHS tape files in `../tapes/`:

```bash
# Install VHS
brew install vhs  # macOS
# or see https://github.com/charmbracelet/vhs

# Generate a GIF
cd packages/plugin/assets/tapes
vhs morning-routine.tape
```

## Design Guidelines

**Color Palette (Bubblegum):**
- Primary: `#F5A3C7` (soft pink)
- Secondary: `#A78BFA` (purple)
- Accent: `#5EEAD4` (teal)
- Background: Dark terminal theme

**Style:**
- Charmbracelet-inspired playful aesthetic
- Clean terminal recordings
- Minimal text, let visuals demonstrate
```

**Step 2: Commit**

```bash
git add packages/plugin/assets/images/README-ASSETS.md
git commit -m "docs(assets): add visual assets documentation (#184)"
```

---

## Task 9: Final Review and Push

**Step 1: Review all changes**

Run: `git log --oneline -10`
Expected: 8 commits for this feature

**Step 2: Run sync script one more time**

Run: `cd packages/plugin && python scripts/sync-readme.py`
Expected: No changes or updated counts

**Step 3: Push all changes**

```bash
git push origin master
```

**Step 4: Verify CI passes**

Run: `gh run list --limit 3`
Expected: All workflows passing

---

## Summary

| Task | Deliverable |
|------|-------------|
| 1 | Asset directory structure |
| 2 | Morning routine VHS tape |
| 3 | Before/after VHS tape |
| 4 | Auto-gen sync script |
| 5 | Rewritten README |
| 6 | Synced auto-gen sections |
| 7 | CI workflow for sync |
| 8 | Asset documentation |
| 9 | Final review and push |

**Next Steps After Implementation:**
1. Generate actual banner image (design work)
2. Install VHS and generate GIFs from tape files
3. Upload images to public repo
4. Create issues for Phases 2-5 (future doc system)
