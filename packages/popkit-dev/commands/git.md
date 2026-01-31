---
description: "commit | push | pr | review | ci | release | publish | prune | finish [--draft, --squash]"
argument-hint: "<subcommand> [options]"
---

# /popkit-dev:git - Git Workflow Management

Git operations with smart commits, PRs, code review, CI/CD, releases, publishing, and branch cleanup.

## Subcommands

| Subcommand | Description                                             |
| ---------- | ------------------------------------------------------- |
| commit     | Smart commit with auto-generated message (default)      |
| push       | Push current branch to remote                           |
| pr         | Pull request management (create, list, view, merge)     |
| review     | Code review with confidence-based filtering             |
| ci         | GitHub Actions workflow runs (list, view, rerun, watch) |
| release    | GitHub releases (create, list, view, changelog)         |
| publish    | Publish plugin to public repo (monorepo → open source)  |
| prune      | Remove stale local branches after PR merge              |
| finish     | Complete development with 4-option flow                 |
| analyze-strategy | Analyze repository branching strategy              |

---

## commit (default)

Generate commit message from staged changes following conventional commits.

Invokes **git commit** with: Status check → Analyze changes → Generate message → Commit with attribution.

**Output:** Conventional commit with Claude Code attribution and Co-Authored-By header.

**Options:** --amend

---

## push

Push current branch to remote with branch protection safety checks.

**Branch Protection (Issue #141, #142):**

Before pushing, MUST check current branch:

```bash
current_branch=$(git branch --show-current 2>/dev/null)
```

**Protected Branches:** `main`, `master`, `develop`, `production`

**If on protected branch:**

1. ❌ BLOCK the push operation (do not just warn)
2. Explain why: "Cannot push directly to protected branch '[branch]' due to branch protection policy"
3. Recommend feature branch workflow:

   ```bash
   # Create feature branch from current state
   git checkout -b feat/descriptive-name
   git push -u origin feat/descriptive-name

   # Create pull request
   gh pr create --title "..." --body "..."

   # Clean up local protected branch
   git checkout [protected-branch]
   git reset --hard origin/[protected-branch]
   ```

4. Reference: See CLAUDE.md "Git Workflow Principles" section

**If on feature branch:**

- Proceed with push
- Use `--force-with-lease` if --force requested
- Confirm if branch has no upstream
- Set upstream with -u flag if needed

**Options:** --force-with-lease, -u

---

## pr

Pull request management via `gh` CLI.

| Subcommand       | Description                              |
| ---------------- | ---------------------------------------- |
| create (default) | Create PR from current branch            |
| list             | List open/all/draft PRs                  |
| view             | View PR details, comments, files, checks |
| merge            | Merge with squash/rebase options         |
| checkout         | Check out PR locally                     |
| diff             | View PR diff                             |
| ready            | Mark draft as ready                      |
| update           | Update PR branch with base               |

**Process (create):** Verify clean state → Create/switch branch → Stage → Commit → Push → **Validate labels (Issue #96)** → Create PR with template.

**Options:** --draft, --base <branch>, --title <text>, --label <labels>, --squash, --rebase, --delete-branch

### Label Validation for PR Creation (Issue #96)

**CRITICAL:** Always validate labels BEFORE calling `gh pr create` to prevent errors.

**Implementation:**

```python
from popkit_shared.utils.github_validator import validate_labels
from popkit_shared.utils.github_cache import GitHubCache

# 1. Determine labels (from flags or branch prefix)
if user_labels:
    requested_labels = user_labels  # e.g., ["enhancement", "needs-review"]
else:
    # Infer from branch name
    branch_name = get_current_branch()
    requested_labels = infer_labels_from_branch(branch_name)
    # feat/* → ["enhancement"]
    # fix/* → ["bug"]
    # docs/* → ["documentation"]

# 2. Validate using cache
cache = GitHubCache()
valid, invalid, suggestions = validate_labels(requested_labels, cache)

# 3. Handle invalid labels
if invalid:
    print(f"⚠️  Invalid labels: {', '.join(invalid)}")

    # Auto-fix with suggestions
    fixed_labels = valid.copy()
    for s in suggestions:
        if s['suggestions']:
            best_match = s['suggestions'][0]
            fixed_labels.append(best_match)
            print(f"   Auto-corrected: {s['invalid']} → {best_match}")

    labels_to_use = fixed_labels
else:
    labels_to_use = valid

# 4. Create PR with validated labels
if labels_to_use:
    gh pr create --title "..." --body "..." --label {','.join(labels_to_use)}
else:
    gh pr create --title "..." --body "..."
```

**Example Output:**

```
Creating PR from branch: feat/user-auth

Inferred labels from branch: enhancement
⚠️  Invalid labels: enhancement
   Auto-corrected: enhancement → feature

✓ Using labels: feature
✓ PR #45 created successfully
```

---

## review

Code review with confidence-based issue filtering (80+ threshold).

Invokes **code-reviewer** agent: Gather changes → Analyze (Simplicity/Bugs/Conventions) → Score → Report critical/important issues only.

**Output:** Categorized issues with confidence scores, file locations, and fix suggestions.

**Options:** --staged, --branch <name>, --pr <number>, --file <path>, --focus <category>, --threshold <score>, --verbose

---

## ci

Monitor and manage GitHub Actions workflows via `gh run` CLI.

| Subcommand     | Description             |
| -------------- | ----------------------- |
| list (default) | Recent workflow runs    |
| view           | View run details, logs  |
| rerun          | Rerun all/failed jobs   |
| watch          | Watch running workflow  |
| cancel         | Cancel running workflow |
| download       | Download artifacts      |
| logs           | View logs               |

**Status icons:** [ok] success, [x] failure, [...] in_progress, [ ] queued, [~] cancelled, [!] skipped

**Options:** --workflow <file>, --branch <name>, --status <state>, --limit <num>, --failed, --job <name>

---

## release

Create and manage GitHub releases with auto-generated changelogs via `gh release` CLI.

| Subcommand     | Description                        |
| -------------- | ---------------------------------- |
| list (default) | All releases                       |
| create         | Create release with auto-changelog |
| view           | View release details               |
| edit           | Edit release notes/status          |
| delete         | Delete release/tag                 |
| changelog      | Preview changelog                  |

**Process (create):** Parse commits → Generate changelog → Update CLAUDE.md (if --update-docs) → Create tag → Create GitHub release.

**Changelog:** Parses conventional commits (feat, fix, docs, perf, refactor, test, chore) and groups by type.

**Version detection:** package.json, Cargo.toml, latest tag + increment.

**Options:** --draft, --prerelease, --title <text>, --update-docs, --changelog-only

---

## publish

Publish plugin from private monorepo to public `jrc1883/popkit-plugin` repo via `git subtree split`.

**Architecture:** Split-repo model - private monorepo (full dev) → public plugin repo (open source).

**Process:** Verify clean state → IP leak scan → Subtree split → Push to public main branch → Optional tag.

**IP Leak Scanner:** Blocks publish on critical/high severity findings. Use `--skip-ip-scan` only for false positives.

**Options:** --dry-run, --branch <name>, --tag <version>, --force, --changelog, --skip-ip-scan

**Remote setup:** `git remote add plugin-public https://github.com/jrc1883/popkit-plugin.git`

---

## prune

Remove stale local branches after PRs are merged.

**Process:** Fetch --prune → Find gone branches → Preview → Delete (if confirmed).

**Safety:** Uses `-d` (safe delete), won't delete unmerged branches, never deletes main/master/develop.

**Options:** --dry-run, --force

---

## finish

Guide completion of development work with structured options.

Invokes **pop-finish-branch**: Verify tests → Present 4 options (merge locally, create PR, keep as-is, discard).

**Options:**

1. Merge back to main locally
2. Push and create Pull Request
3. Keep branch as-is
4. Discard work (requires typed confirmation)

---

## analyze-strategy

Analyze repository branching strategy and provide recommendations.

**Phase 1 Implementation (Issue #151):**

Detects current branching strategy by analyzing:
- Branch naming patterns (feat/*, fix/*, release/*, hotfix/*)
- Long-lived vs ephemeral branches
- Merge patterns (direct to main, via develop, etc.)
- GitHub branch protection rules
- Average branch lifetime

**Supported Strategies:**
- **Trunk-based Development**: Direct merges to main, short-lived feature branches
- **GitHub Flow**: Feature branches + main, continuous deployment
- **Git Flow**: Multiple long-lived branches (main, develop, release/*, hotfix/*)
- **GitLab Flow**: Environment-based branches (main, staging, production)
- **Custom/Unknown**: Non-standard patterns

**Output:**
```
# Git Branch Strategy Analysis

**Detected Strategy**: Trunk-based Development
**Confidence**: 80%

## Evidence
- main as primary branch
- 32 feature branches
- short-lived branches (avg 3 days)

## Branch Statistics
- Total branches: 35
- Feature branches: 32
- Bugfix branches: 3
- Average branch lifetime: 3 days

## Recommendations
✅ Good for: Small teams (2-5 developers), rapid iteration
✅ Benefits: Fast merges, simple workflow, continuous integration
💡 Consider Git Flow if: Need release coordination or multiple version support
```

**Technical Implementation:**
- Uses `popkit_shared.utils.git_strategy.GitStrategyDetector`
- Analyzes all local and remote branches
- Queries GitHub API for protection rules (via `gh` CLI)
- Calculates confidence scores based on pattern matching

**Options:** --json (output JSON format), --verbose (detailed branch info)

**Related Commands:**
- Phase 2: `/popkit-dev:git recommend-strategy` (interactive questionnaire)
- Phase 3: `/popkit-dev:git migrate-to <strategy>` (automated migration)
- Phase 4: Hooks for branch naming validation

---

## Git Safety Protocol

| Rule        | Action                                         |
| ----------- | ---------------------------------------------- |
| Config      | NEVER update git config                        |
| Destructive | NEVER run without explicit request             |
| Hooks       | NEVER skip (--no-verify) unless requested      |
| Force push  | NEVER to main/master                           |
| Amend       | AVOID unless requested, check authorship first |
| Preview     | ALWAYS before bulk operations                  |

---

## Architecture

| Component    | Integration                                  |
| ------------ | -------------------------------------------- |
| Commit       | Conventional commits, attribution            |
| PR Templates | output-styles/pr-description.md              |
| Code Review  | skills/pop-code-review/, agent code-reviewer |
| Finish Flow  | skills/pop-finish-branch/                    |
| GitHub CLI   | gh pr/run/release commands                   |
| Changelog    | hooks/utils/changelog_generator.py           |
| Version      | package.json, Cargo.toml, git tags           |
| Publishing   | git subtree split, IP scanner                |
| IP Scanner   | hooks/utils/ip_protection.py                 |

**Related:** /popkit-dev:worktree, /popkit-dev:dev execute, /popkit:morning

## Examples

See examples/git/ for: commit-examples.md, pr-examples.md, review-examples.md, ci-examples.md, release-examples.md, publish-examples.md.
