# Git Commit Examples

## Basic Usage

```bash
/popkit:git                           # Auto-generate commit message
/popkit:git commit                    # Same as above
/popkit:git commit "fixed the login"  # Use hint for message
/popkit:git commit --amend            # Amend previous commit
```

## Process

1. **Check Status**
   ```bash
   git status --porcelain
   git diff --cached --stat
   ```

2. **Analyze Changes**
   - Count files changed
   - Identify change types (new, modified, deleted)
   - Detect patterns (feat, fix, refactor, etc.)

3. **Generate Message**
   Following conventional commits:
   ```
   <type>(<scope>): <subject>

   <body>

   <footer>
   ```
   Types: feat, fix, docs, style, refactor, perf, test, chore, ci, revert

4. **Commit**
   ```bash
   git commit -m "$(cat <<'EOF'
   <generated message>

   Generated with Claude Code

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

## Attribution

All commits include:
- Claude Code attribution link
- Co-Authored-By header
