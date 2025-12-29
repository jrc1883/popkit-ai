# PopKit v1.0.0-beta.1 Beta Testing Checklist

This checklist helps beta testers systematically test all major features. Check off items as you test them.

---

## Pre-Testing Setup

- [ ] Claude Code version 2.0.67+ installed
- [ ] Python 3.8+ installed and in PATH
- [ ] Git installed and configured
- [ ] Test project prepared (or using existing project)
- [ ] PopKit plugins installed
- [ ] Claude Code restarted after installation
- [ ] Installation verified with `/popkit:plugin test`

---

## Installation Testing

### Complete Suite Installation
- [ ] `/plugin install popkit-suite@jrc1883/popkit-claude` succeeds
- [ ] All 5 plugins loaded (verify with `/plugin list`)
- [ ] No error messages during installation
- [ ] Restart completes successfully
- [ ] All commands available after restart

### Selective Installation
- [ ] Install popkit-core only
- [ ] Verify popkit-core commands work
- [ ] Add popkit-dev
- [ ] Verify both cores and dev commands work
- [ ] Add popkit-ops
- [ ] Verify all three sets of commands work
- [ ] Add popkit-research
- [ ] Verify all commands work together

### Uninstall/Reinstall
- [ ] Uninstall all plugins
- [ ] Verify commands removed
- [ ] Reinstall popkit-suite
- [ ] Verify everything works again

---

## Core Plugin (popkit-core)

### Project Commands
- [ ] `/popkit:project analyze` - Analyzes project correctly
- [ ] `/popkit:project init` - Initializes new project
- [ ] `/popkit:project embed` - Creates embeddings
- [ ] `/popkit:project generate` - Generates MCP server

### Plugin Commands
- [ ] `/popkit:plugin test` - Runs tests successfully
- [ ] `/popkit:plugin test --verbose` - Shows detailed output
- [ ] `/popkit:plugin docs` - Shows documentation
- [ ] `/popkit:plugin sync` - Syncs plugin state

### Power Mode
- [ ] `/popkit:power init` - Sets up Power Mode
- [ ] `/popkit:power start` - Starts orchestration
- [ ] `/popkit:power stop` - Stops orchestration
- [ ] `/popkit:power status` - Shows current status
- [ ] Native async mode works (without Redis)
- [ ] Status line shows accurate info

### Dashboard
- [ ] `/popkit:dashboard` - Shows project overview
- [ ] `/popkit:dashboard add` - Adds new project
- [ ] `/popkit:dashboard remove` - Removes project
- [ ] `/popkit:dashboard switch` - Switches projects

### Other Core Commands
- [ ] `/popkit:stats` - Shows usage statistics
- [ ] `/popkit:privacy` - Privacy controls work
- [ ] `/popkit:account` - Account management works
- [ ] `/popkit:upgrade` - Upgrade prompts work
- [ ] `/popkit:bug` - Bug reporter works

---

## Dev Plugin (popkit-dev)

### Feature Development
- [ ] `/popkit:dev "description"` - Full 7-phase workflow
- [ ] Phase 1: Discovery completes
- [ ] Phase 2: Exploration (code-explorer) works
- [ ] Phase 3: Questions asked
- [ ] Phase 4: Architecture (code-architect) created
- [ ] Phase 5: Implementation executes
- [ ] Phase 6: Review (code-reviewer) catches issues
- [ ] Phase 7: Summary provided
- [ ] `/popkit:dev work #123` - Works with GitHub issues
- [ ] `/popkit:dev brainstorm` - Brainstorming works
- [ ] `/popkit:dev plan` - Planning works
- [ ] `/popkit:dev execute` - Execution works

### Git Operations
- [ ] `/popkit:git commit` - Creates good commit messages
- [ ] `/popkit:git push` - Pushes to remote
- [ ] `/popkit:git pr` - Creates pull request
- [ ] `/popkit:git pr list` - Lists PRs
- [ ] `/popkit:git pr view <num>` - Views PR details
- [ ] `/popkit:git pr merge <num>` - Merges PR
- [ ] `/popkit:git review` - Reviews code
- [ ] `/popkit:git review --pr <num>` - Reviews specific PR
- [ ] `/popkit:git ci` - Shows CI runs
- [ ] `/popkit:git ci view <num>` - Shows run details
- [ ] `/popkit:git ci rerun <num>` - Reruns failed jobs
- [ ] `/popkit:git release` - Lists releases
- [ ] `/popkit:git release create` - Creates release
- [ ] `/popkit:git prune` - Cleans up branches
- [ ] `/popkit:git finish` - Completes workflow

### Routine Management
- [ ] `/popkit:routine morning` - Morning health check
- [ ] Morning routine shows Ready to Code score
- [ ] Morning routine detects issues accurately
- [ ] `/popkit:routine morning quick` - One-line summary
- [ ] `/popkit:routine nightly` - Nightly cleanup
- [ ] Nightly routine shows Sleep Score
- [ ] Nightly routine suggests cleanup
- [ ] `/popkit:routine morning generate` - Creates custom routine
- [ ] `/popkit:routine morning list` - Lists routines
- [ ] `/popkit:routine morning set <id>` - Sets default

### Issue Management
- [ ] `/popkit:issue create` - Creates GitHub issue
- [ ] `/popkit:issue list` - Lists issues
- [ ] `/popkit:issue view <num>` - Views issue
- [ ] `/popkit:issue close <num>` - Closes issue
- [ ] `/popkit:issue comment <num>` - Adds comment

### Milestone Management
- [ ] `/popkit:milestone list` - Lists milestones
- [ ] `/popkit:milestone create` - Creates milestone
- [ ] `/popkit:milestone report` - Shows progress
- [ ] `/popkit:milestone health` - Health analysis

### Worktree Management
- [ ] `/popkit:worktree create <branch>` - Creates worktree
- [ ] `/popkit:worktree list` - Lists worktrees
- [ ] `/popkit:worktree remove <branch>` - Removes worktree

### Next Action
- [ ] `/popkit:next` - Recommends next actions
- [ ] `/popkit:next quick` - Quick recommendations

---

## Ops Plugin (popkit-ops)

### Assessment
- [ ] `/popkit:assess all` - Runs all assessments
- [ ] `/popkit:assess anthropic` - Anthropic compliance
- [ ] `/popkit:assess security` - Security audit
- [ ] `/popkit:assess performance` - Performance check
- [ ] `/popkit:assess ux` - UX review
- [ ] `/popkit:assess architect` - Architecture review
- [ ] `/popkit:assess docs` - Documentation check
- [ ] Assessment scores are reasonable
- [ ] Issues found are actionable

### Audit
- [ ] `/popkit:audit health` - Health audit
- [ ] `/popkit:audit stale` - Finds stale code
- [ ] `/popkit:audit duplicates` - Finds duplicates
- [ ] `/popkit:audit ip-leak` - Scans for leaks
- [ ] Audit results are accurate

### Debug
- [ ] `/popkit:debug code` - Systematic debugging
- [ ] `/popkit:debug routing` - Agent routing debug
- [ ] Debug output is helpful

### Security
- [ ] `/popkit:security scan` - Security scan
- [ ] `/popkit:security list` - Lists vulnerabilities
- [ ] `/popkit:security fix` - Auto-fix issues
- [ ] `/popkit:security report` - Generates report

### Deploy
- [ ] `/popkit:deploy init` - Initializes deployment
- [ ] `/popkit:deploy setup` - Sets up targets
- [ ] `/popkit:deploy validate` - Validates config
- [ ] `/popkit:deploy execute` - Executes deployment
- [ ] `/popkit:deploy rollback` - Rolls back

---

## Research Plugin (popkit-research)

### Research Capture
- [ ] `/popkit:research capture` - Captures research
- [ ] `/popkit:research list` - Lists research items
- [ ] `/popkit:research search <query>` - Searches research
- [ ] `/popkit:research tag` - Tags research
- [ ] `/popkit:research show <id>` - Shows item details
- [ ] `/popkit:research delete <id>` - Deletes item
- [ ] `/popkit:research merge` - Merges items

### Knowledge Base
- [ ] `/popkit:knowledge add` - Adds knowledge
- [ ] `/popkit:knowledge list` - Lists knowledge
- [ ] `/popkit:knowledge search <query>` - Searches knowledge
- [ ] `/popkit:knowledge remove <id>` - Removes item
- [ ] `/popkit:knowledge sync` - Syncs to cloud

---

## Cross-Plugin Integration

### Workflow Integration
- [ ] Morning routine → Next action → Dev workflow
- [ ] Dev workflow → Git commit → PR → Review
- [ ] Security scan → Fix → Commit → Deploy
- [ ] Research → Knowledge base → Project analysis

### State Persistence
- [ ] Session state saves correctly
- [ ] Resume from previous session works
- [ ] Context restored accurately

### Power Mode Coordination
- [ ] Multiple agents coordinate properly
- [ ] Message passing works
- [ ] No race conditions
- [ ] Status updates are accurate

---

## Edge Cases & Error Handling

### Project Types
- [ ] Works with Next.js project
- [ ] Works with React project
- [ ] Works with Python project
- [ ] Works with monorepo
- [ ] Works with non-standard structure
- [ ] Works with no package.json

### Error Scenarios
- [ ] Handles missing dependencies gracefully
- [ ] Recovers from network errors
- [ ] Handles git conflicts properly
- [ ] Shows helpful error messages
- [ ] Doesn't crash on unexpected input

### Performance
- [ ] Works well with large projects (1000+ files)
- [ ] Morning routine completes in <30s
- [ ] Embeddings generate in <2min
- [ ] No memory leaks during long sessions
- [ ] Context usage is reasonable (<20k tokens)

---

## Documentation & Help

- [ ] `/popkit:help` shows helpful information
- [ ] README files are accurate
- [ ] Examples in docs work correctly
- [ ] CLAUDE.md is up to date
- [ ] Marketplace descriptions are clear

---

## User Experience

### Command Discovery
- [ ] Commands are easy to find
- [ ] Tab completion works
- [ ] Help text is clear

### Error Messages
- [ ] Errors are informative
- [ ] Suggest fixes when possible
- [ ] Include relevant context

### Output Formatting
- [ ] ASCII dashboards render correctly
- [ ] Markdown tables format properly
- [ ] Colors/formatting enhance readability
- [ ] Output is concise but complete

---

## Regression Testing

### Breaking Changes
- [ ] All v0.x commands still work
- [ ] Workflows haven't regressed
- [ ] Performance hasn't degraded

### Backwards Compatibility
- [ ] Old config files still work
- [ ] Existing projects compatible
- [ ] Migration from monolithic plugin works

---

## Final Checks

- [ ] All critical paths tested
- [ ] At least 3 edge cases tested
- [ ] Feedback submitted for any issues
- [ ] Documentation gaps reported
- [ ] Performance noted (good or bad)

---

## Post-Testing

- [ ] Submit comprehensive feedback
- [ ] Share testing results
- [ ] Report any critical bugs immediately
- [ ] Suggest improvements
- [ ] Rate overall experience (1-10): ___

---

## Notes

Use this section for additional observations:

```
[Your notes here]
```

---

**Testing Date**: _______________
**Tester**: _______________
**Environment**: _______________
**Overall Status**: [ ] Pass [ ] Pass with issues [ ] Fail
