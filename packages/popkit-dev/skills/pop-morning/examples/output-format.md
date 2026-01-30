# Output Format

Example morning routine report.

```markdown
# ☀️ Morning Routine Report

**Date**: 2025-12-28 09:30
**Ready to Code Score**: 75/100 👍
**Grade**: B - Good - Ready with minor issues

## Score Breakdown

| Check                | Points | Status                               |
| -------------------- | ------ | ------------------------------------ |
| Session Restored     | 20/20  | ✅ Previous session context restored |
| Services Healthy     | 10/20  | ⚠️ Missing: redis                    |
| Dependencies Updated | 15/15  | ✅ All dependencies up to date       |
| Branches Synced      | 10/15  | ⚠️ 3 commits behind remote           |
| PRs Reviewed         | 15/15  | ✅ No PRs pending review             |
| Issues Triaged       | 10/15  | ⚠️ 2 issues need triage              |

## 🔧 Dev Services Status

**Required**: 2 services
**Running**: 1 services

**Not Running:**

- redis

## 🔄 Branch Sync Status

**Current Branch**: fix/critical-build-blockers
**Commits Behind Remote**: 3

Run `git pull` to sync with remote.

## 📋 Recommendations

**Before Starting Work:**

- Start dev services: redis
- Sync with remote: git pull (behind by 3 commits)

**Today's Focus:**

- Triage 2 open issues
- Review overnight commits and CI results
- Continue: Fix critical build blockers

---

STATUS.json updated ✅
Morning session initialized. Ready to code!
```

## Quick Summary Format

```bash
Ready to Code Score: 75/100 👍 - redis down, 3 commits behind
```
