# Account Command Consolidation Plan

**Date:** 2025-12-29
**Epic:** TBD
**Status:** Design
**Author:** Claude Sonnet 4.5

---

## Executive Summary

Consolidate three fragmented account-related commands (`/popkit:account`, `/popkit:upgrade`, `/popkit:cloud`) into a single, cohesive `/popkit:account` command with clear subcommands for all account management tasks.

**Current State:** Three commands with overlapping functionality and confusing user paths.
**Target State:** One command with intuitive subcommands following PopKit's standard patterns.

---

## 1. Current State Analysis

### `/popkit:account` (packages/popkit-core/commands/account.md)

**Purpose:** View and manage PopKit account
**Status:** ✅ In plugin.json
**Subcommands:**
- `status` (default) - Show API key status and available enhancements
- `usage` - Detailed feature usage and rate limits (Issue #138)
- `keys` - List and manage API keys
- `logout` - Clear local session/cache

**Implementation:**
- Pure markdown command specification
- Queries `POPKIT_API_KEY` env var
- Calls cloud API endpoints: `/v1/health`, `/v1/usage/summary`, `/v1/account/keys`
- No backing skill (implementation is inline Python/Bash)

**Key Features:**
- API key status checking
- Feature usage tracking
- Enhancement status display (semantic routing, pattern learning, etc.)
- Dual mode: with/without API key

---

### `/popkit:upgrade` (packages/popkit-core/commands/upgrade.md)

**Purpose:** Get free API key for enhanced intelligence
**Status:** ✅ In plugin.json
**Subcommands:** None (single action)
**Flags:**
- `--open` - Force open in browser (default)
- `--url` - Just print the URL

**Implementation:**
- Opens `https://popkit.dev/signup` in browser
- Uses AskUserQuestion to confirm
- Cross-platform browser opening (macOS/Windows/Linux)
- Shows next steps after opening

**Key Features:**
- Browser-based signup flow
- Environment variable setup instructions
- Feature comparison (with/without API key)

**Overlap with other commands:**
- References `/popkit:cloud signup` as alternative
- References `/popkit:account status` for verification
- Duplicates cloud signup messaging

---

### `/popkit:cloud` (packages/popkit-core/commands/cloud.md)

**Purpose:** Manage PopKit Cloud connection
**Status:** ⚠️ **NOT in plugin.json** (orphaned file!)
**Subcommands:**
- `signup` - Create new account and get API key
- `login` - Login to existing account
- `status` (default) - Show cloud connection status
- `logout` - Disconnect and clear API key

**Implementation:**
- `signup` subcommand invokes `pop-cloud-signup` skill (packages/popkit-core/skills/pop-cloud-signup/SKILL.md)
- `status` queries cloud API: `/v1/status`
- `login` and `logout` have inline Python implementations
- Manages `.claude/popkit/cloud-config.json` (chmod 600)

**Key Features:**
- Full signup/login workflow
- Secure API key storage (config file + env var)
- Connection testing
- Detailed cloud status reporting

**Overlap with other commands:**
- `cloud status` duplicates `account status` functionality
- `cloud logout` duplicates `account logout` functionality
- `cloud signup` duplicates `upgrade` functionality

---

### Supporting Skill: `pop-cloud-signup`

**Location:** packages/popkit-core/skills/pop-cloud-signup/SKILL.md
**Status:** ✅ Exists and functional
**Purpose:** Create PopKit Cloud account, generate API key, configure local connection

**Process:**
1. Check for existing cloud config
2. Collect email/password via AskUserQuestion
3. POST to `https://api.thehouseofdeals.com/v1/auth/signup`
4. Save API key to `.claude/popkit/cloud-config.json` (chmod 600)
5. Test connection via `/v1/health`
6. Display setup instructions

**Key Features:**
- Comprehensive error handling
- Secure credential collection
- Config file management
- Connection validation

---

### Related Command: `/popkit:privacy`

**Location:** packages/popkit-core/commands/privacy.md
**Status:** ✅ In plugin.json
**Purpose:** Privacy controls for data sharing

**Subcommands:**
- `status` - View privacy settings
- `consent` - Give/revoke consent
- `settings` - Update privacy settings
- `export` - GDPR data export
- `delete` - GDPR data deletion

**Relationship:** Privacy is separate from account management but related. Should remain its own command.

---

### Overlapping Functionality Summary

| Feature | `/popkit:account` | `/popkit:upgrade` | `/popkit:cloud` |
|---------|-------------------|-------------------|-----------------|
| Show API key status | ✅ `status` | ❌ | ✅ `status` |
| Show usage stats | ✅ `usage` | ❌ | ✅ (in status) |
| Manage API keys | ✅ `keys` | ❌ | ❌ |
| Signup for account | ❌ | ✅ (browser) | ✅ `signup` |
| Login to account | ❌ | ❌ | ✅ `login` |
| Logout/clear session | ✅ `logout` | ❌ | ✅ `logout` |
| Open browser to signup | ❌ | ✅ | ❌ |
| Test cloud connection | ✅ (via status) | ❌ | ✅ `status` |

**Duplication:** 40-50% feature overlap, causing user confusion about which command to use.

---

## 2. Proposed New Structure

### `/popkit:account` - Unified Command

**All-in-one account management command with clear subcommands.**

#### Subcommands

| Subcommand | Description | Implementation Source |
|------------|-------------|-----------------------|
| `status` (default) | Show account status, API key, cloud connection, usage | Merge `account status` + `cloud status` |
| `signup` | Create new PopKit account and get API key | From `cloud signup` (uses `pop-cloud-signup` skill) |
| `login` | Login to existing account | From `cloud login` |
| `keys` | List and manage API keys | From `account keys` |
| `usage` | Detailed feature usage and rate limits | From `account usage` |
| `logout` | Disconnect from cloud and clear local session | Merge `account logout` + `cloud logout` |

#### Removed Commands

- **`/popkit:upgrade`** → Deprecated, functionality merged into `/popkit:account signup`
- **`/popkit:cloud`** → Deprecated, all functionality moved to `/popkit:account`

#### Migration Path

**Backward Compatibility (Phase 1 - 2 releases):**
```markdown
# In upgrade.md and cloud.md
---
name: upgrade
deprecated: true
redirect: account signup
---

⚠️ **Deprecated:** This command has been replaced.

Use `/popkit:account signup` instead.

This command will be removed in v1.2.0.
```

**Removal (Phase 2 - after 2 releases):**
- Delete `upgrade.md` and `cloud.md` files
- Remove from plugin.json

---

## 3. Detailed Subcommand Specifications

### `status` (default)

**Merge:** `account status` + `cloud status`

**Purpose:** Show comprehensive account information in one view

**Implementation:**
```python
# 1. Check API key (env var + config file)
api_key = os.environ.get("POPKIT_API_KEY") or read_from_config()

# 2. Query cloud status (if API key exists)
if api_key:
    response = requests.get("https://api.thehouseofdeals.com/v1/status",
                           headers={"Authorization": f"Bearer {api_key}"})

# 3. Display unified status
```

**Output (with API key):**
```markdown
✅ PopKit Account Connected

**Email:** user@example.com
**API Key:** ******def456 (configured via environment)
**Cloud Status:** Connected (82ms)

### Available Features
- All core workflows: ✅ (always available locally)
- Semantic agent routing: ✅ (enhanced with cloud)
- Community pattern learning: ✅ (enhanced with cloud)
- Cloud knowledge base: ✅ (enhanced with cloud)
- Cross-project insights: ✅ (enhanced with cloud)

### Usage This Month
- API calls: 1,234 / ∞
- Embeddings: 456
- Pattern queries: 89
- Patterns stored: 156

**API Key Source:** Environment variable (`POPKIT_API_KEY`)

Run `/popkit:account usage` for detailed breakdown.
```

**Output (without API key):**
```markdown
⚪ No PopKit Account

**Status:** Working locally (fully functional)

### Available Features
- All core workflows: ✅ (full functionality)
- Semantic agent routing: ⚪ (keyword-based only)
- Community pattern learning: ⚪ (local only)
- Cloud knowledge base: ⚪ (not available)
- Cross-project insights: ⚪ (not available)

### Get Cloud Enhancements

Run `/popkit:account signup` to create a free account and enable:
- Semantic agent routing via embeddings
- Community pattern learning across projects
- Cloud-backed knowledge base
- Cross-project insights

**Note:** All workflows work without cloud. The API key adds semantic intelligence.
```

---

### `signup`

**Source:** `cloud signup` (uses `pop-cloud-signup` skill)

**Purpose:** Create new PopKit Cloud account

**Implementation:**
```markdown
Invoke the `pop-cloud-signup` skill via Skill tool:

Use Skill tool with skill="popkit:pop-cloud-signup"
```

**Process:**
1. Check for existing config (warn if found)
2. Collect email/password via AskUserQuestion
3. POST to cloud signup endpoint
4. Save API key securely
5. Test connection
6. Display success + next steps

**Output:** (from skill)
```markdown
✅ PopKit Account Created

**Email:** user@example.com
**API Key:** pk_live_abc123... (saved securely)

Your API key is saved to ~/.claude/popkit/cloud-config.json

### Quick Start

1. Verify connection:
   /popkit:account status

2. Cloud enhancements are now active ✅

Run `/popkit:account` to see your account status.
```

---

### `login`

**Source:** `cloud login`

**Purpose:** Login to existing PopKit Cloud account

**Implementation:**
```python
# 1. Check for existing config (warn if found)
config_path = Path.home() / ".claude/popkit/cloud-config.json"
if config_path.exists():
    # Confirm overwrite via AskUserQuestion

# 2. Collect email/password
# Use AskUserQuestion for email and password

# 3. POST to login endpoint
response = requests.post(
    "https://api.thehouseofdeals.com/v1/auth/login",
    json={"email": email, "password": password}
)

# 4. Save API key
if response.status_code == 200:
    save_to_config(api_key, email)

# 5. Display success
```

**Output:**
```markdown
✅ Logged in to PopKit

**Email:** user@example.com
**API Key:** pk_live_xyz789... (saved securely)

Run `/popkit:account status` to verify connection.
```

---

### `keys`

**Source:** `account keys` (unchanged)

**Purpose:** List and manage API keys

**Implementation:**
```bash
curl -s -H "Authorization: Bearer $POPKIT_API_KEY" \
  https://api.thehouseofdeals.com/v1/account/keys
```

**Output:**
```markdown
## Your API Keys

| Name | Key | Last Used |
|------|-----|-----------|
| Default Key | pk_live_...abc123 | 2 hours ago |
| CI Pipeline | pk_live_...def456 | 1 day ago |

### Actions
```

Then use AskUserQuestion:
- "Create new key"
- "Revoke a key"
- "Done"

---

### `usage`

**Source:** `account usage` (unchanged)

**Purpose:** Detailed feature usage and rate limits

**Implementation:**
```bash
curl -s -H "Authorization: Bearer $POPKIT_API_KEY" \
  https://api.thehouseofdeals.com/v1/usage/summary
```

**Output:**
```markdown
## Feature Usage

**Period:** December 2025

### This Month's Usage

| Feature | Used | Notes |
|---------|------|-------|
| API Calls | 1,234 | Cloud enhancements active |
| Embeddings | 456 | Semantic agent routing |
| Pattern Queries | 89 | Community knowledge base |
| Knowledge Base Access | 125 | Cross-project insights |

### Enhancement Status

All enhancements active. ✅
```

---

### `logout`

**Merge:** `account logout` + `cloud logout`

**Purpose:** Disconnect from cloud and clear local session

**Implementation:**
```python
# 1. Check for config or env var
config_path = Path.home() / ".claude/popkit/cloud-config.json"
has_config = config_path.exists()
has_env = os.environ.get("POPKIT_API_KEY")

if not has_config and not has_env:
    print("⚪ Not connected to PopKit")
    return

# 2. Confirm logout via AskUserQuestion
# question: "Disconnect from PopKit Cloud?"
# options: ["Yes, logout", "No, cancel"]

# 3. Delete config file
if config_path.exists():
    config_path.unlink()

# 4. Remind about env var
if has_env:
    print("⚠️  POPKIT_API_KEY environment variable is still set")
    print("Unset it in your shell:")
    print("  unset POPKIT_API_KEY")

# 5. Display success
```

**Output:**
```markdown
✅ Logged out from PopKit

**Config file:** Deleted
**API key:** Cleared

### What's next?

All workflows continue to work locally.

To reconnect:
- /popkit:account signup - Create new account
- /popkit:account login - Login to existing account
```

---

## 4. Migration Steps

### Phase 1: Create Unified Command (Week 1)

**Files to modify:**

1. **packages/popkit-core/commands/account.md**
   - Add `signup` subcommand (invoke `pop-cloud-signup` skill)
   - Add `login` subcommand (from `cloud.md`)
   - Merge `status` logic from `cloud status`
   - Merge `logout` logic from `cloud logout`
   - Update examples and documentation

2. **packages/popkit-core/commands/upgrade.md**
   - Add deprecation notice at top
   - Add redirect message: "Use `/popkit:account signup` instead"
   - Keep functional for 2 releases

3. **packages/popkit-core/commands/cloud.md**
   - Add deprecation notice at top
   - Add redirect messages for each subcommand
   - Keep functional for 2 releases

4. **packages/popkit-core/.claude-plugin/plugin.json**
   - Keep all three commands listed (for backward compatibility)
   - Add comments indicating deprecation status

**Testing checklist:**
- [ ] `/popkit:account` works without API key
- [ ] `/popkit:account` works with API key
- [ ] `/popkit:account signup` creates account successfully
- [ ] `/popkit:account login` authenticates existing user
- [ ] `/popkit:account keys` lists API keys
- [ ] `/popkit:account usage` shows usage stats
- [ ] `/popkit:account logout` clears session
- [ ] Deprecated commands still work but show warnings

---

### Phase 2: Deprecation Warnings (v1.0.1)

**Files to modify:**

1. **packages/popkit-core/commands/upgrade.md**
   ```markdown
   ---
   name: upgrade
   deprecated: true
   redirect: account signup
   description: "⚠️ DEPRECATED - Use /popkit:account signup instead"
   ---

   # /popkit:upgrade (DEPRECATED)

   ⚠️ **This command is deprecated and will be removed in v1.2.0.**

   **Use `/popkit:account signup` instead.**

   ---

   [Original content with deprecation warnings throughout]
   ```

2. **packages/popkit-core/commands/cloud.md**
   ```markdown
   ---
   name: cloud
   deprecated: true
   redirect: account
   description: "⚠️ DEPRECATED - Use /popkit:account instead"
   ---

   # /popkit:cloud (DEPRECATED)

   ⚠️ **This command is deprecated and will be removed in v1.2.0.**

   **New command structure:**
   - `/popkit:cloud signup` → `/popkit:account signup`
   - `/popkit:cloud login` → `/popkit:account login`
   - `/popkit:cloud status` → `/popkit:account status`
   - `/popkit:cloud logout` → `/popkit:account logout`

   ---

   [Original content with deprecation warnings]
   ```

**Documentation updates:**
- [ ] Update CLAUDE.md command references
- [ ] Update README.md examples
- [ ] Add migration note to CHANGELOG.md
- [ ] Update any docs/plans/*.md files referencing old commands

---

### Phase 3: Removal (v1.2.0 - 2+ releases later)

**Files to delete:**
- `packages/popkit-core/commands/upgrade.md`
- `packages/popkit-core/commands/cloud.md`

**Files to modify:**
- `packages/popkit-core/.claude-plugin/plugin.json` - Remove from commands list

**Final testing:**
- [ ] `/popkit:upgrade` returns "command not found"
- [ ] `/popkit:cloud` returns "command not found"
- [ ] `/popkit:account` has all functionality working
- [ ] All documentation updated

---

## 5. Impact Analysis

### Breaking Changes for Users

**None during Phase 1-2** (deprecation period)

During the deprecation period (2+ releases):
- Old commands continue to work
- Warnings guide users to new command
- No workflow disruption

**After Phase 3 (v1.2.0+):**
- `/popkit:upgrade` no longer available → Breaking change ⚠️
- `/popkit:cloud` no longer available → Breaking change ⚠️
- Users must update to `/popkit:account`

**Migration Guide** (to be published):
```markdown
# Migrating from v1.0.x to v1.2.0

## Command Changes

### Account Management

**Old commands (deprecated):**
```bash
/popkit:upgrade                  # Signup
/popkit:cloud signup             # Signup
/popkit:cloud login              # Login
/popkit:cloud status             # Status
/popkit:cloud logout             # Logout
```

**New unified command:**
```bash
/popkit:account signup           # Create account
/popkit:account login            # Login
/popkit:account status           # Show status
/popkit:account keys             # Manage keys
/popkit:account usage            # Usage stats
/popkit:account logout           # Logout
```

### Why the change?

- **Less confusion:** One command for all account tasks
- **Consistent patterns:** Follows PopKit's subcommand structure
- **Better discovery:** All features in one place
```

---

### Documentation Updates Needed

**Files requiring updates:**

1. **Root documentation:**
   - `README.md` - Update command examples
   - `CLAUDE.md` - Update command references
   - `CHANGELOG.md` - Add migration notes

2. **Package documentation:**
   - `packages/popkit-core/README.md` - Update command list
   - `packages/popkit-suite/README.md` - Update examples

3. **Plans and research:**
   - `docs/plans/2025-12-09-billing-architecture.md` - Mark as deprecated (already noted)
   - Any other files referencing `/popkit:upgrade` or `/popkit:cloud`

4. **Skills:**
   - `packages/popkit-core/skills/pop-cloud-signup/SKILL.md` - Update "When to Use" section

**Search patterns to update:**
```bash
# Find all references to update
grep -r "/popkit:upgrade" packages/
grep -r "/popkit:cloud" packages/
grep -r "popkit:upgrade" docs/
grep -r "popkit:cloud" docs/
```

---

### User Experience Improvements

**Before (confusing):**
- "Do I use `/popkit:upgrade` or `/popkit:cloud signup`?"
- "Where do I check my API key status?"
- "How do I manage my account?"

**After (clear):**
- "Everything is in `/popkit:account`"
- "Run `/popkit:account` to see status"
- "Run `/popkit:account signup` to create account"

**Benefits:**
1. **Single entry point:** All account tasks in one command
2. **Consistent patterns:** Subcommands like `/popkit:project`, `/popkit:power`, etc.
3. **Reduced cognitive load:** Users don't need to remember 3 commands
4. **Better help text:** All options visible in one place

---

## 6. Implementation Checklist

### Week 1: Unified Command Creation

- [ ] Create new `account.md` with all subcommands
  - [ ] Merge `status` from `account.md` + `cloud.md`
  - [ ] Add `signup` subcommand (invoke `pop-cloud-signup` skill)
  - [ ] Add `login` subcommand (from `cloud.md`)
  - [ ] Keep `keys` subcommand (unchanged)
  - [ ] Keep `usage` subcommand (unchanged)
  - [ ] Merge `logout` from `account.md` + `cloud.md`
- [ ] Update all examples and documentation in `account.md`
- [ ] Test all subcommands work correctly
- [ ] Update `pop-cloud-signup` skill "When to Use" section

### Week 2: Deprecation Notices

- [ ] Add deprecation notice to `upgrade.md`
- [ ] Add deprecation notice to `cloud.md`
- [ ] Update CHANGELOG.md with migration notes
- [ ] Test deprecated commands still work but show warnings
- [ ] Update CLAUDE.md command references
- [ ] Update README.md examples

### Week 3: Documentation Sweep

- [ ] Search and update all `/popkit:upgrade` references
- [ ] Search and update all `/popkit:cloud` references
- [ ] Create migration guide document
- [ ] Update package READMEs
- [ ] Update any docs/plans files

### Week 4: Testing & Validation

- [ ] Test signup flow end-to-end
- [ ] Test login flow
- [ ] Test status with/without API key
- [ ] Test keys management
- [ ] Test usage stats
- [ ] Test logout
- [ ] Verify deprecated commands warn users
- [ ] Run `/popkit:plugin test` validation

### Future (v1.2.0): Removal

- [ ] Delete `upgrade.md`
- [ ] Delete `cloud.md`
- [ ] Remove from `plugin.json`
- [ ] Update version to v1.2.0
- [ ] Publish migration guide
- [ ] Test removal doesn't break anything

---

## 7. Open Questions

### 1. Should we keep `cloud.md` at all?

**Option A:** Keep as deprecated file with redirects (current plan)
**Option B:** Delete immediately and rely on error messages
**Option C:** Remove from plugin.json but keep file for reference

**Recommendation:** Option A - Keep for 2 releases with clear deprecation warnings.

### 2. Should `signup` be a top-level shortcut?

**Option A:** Require `/popkit:account signup` (current plan)
**Option B:** Add `/popkit:signup` as alias to `/popkit:account signup`
**Option C:** Keep `/popkit:upgrade` as permanent alias

**Recommendation:** Option A - Consistency is more important than saving a few keystrokes.

### 3. What about the `pop-cloud-signup` skill name?

**Option A:** Keep as `pop-cloud-signup` (current)
**Option B:** Rename to `pop-account-signup`
**Option C:** Create new `pop-account-signup` and deprecate old one

**Recommendation:** Option A - Internal skill names don't need to change; only user-facing commands matter.

### 4. Should we add a `billing` subcommand?

The old `account.md` had a `billing` subcommand placeholder. Should we implement it now?

**Option A:** Add `billing` subcommand (open Stripe portal)
**Option B:** Skip for now (wait for billing implementation)
**Option C:** Add as stub with "Coming soon" message

**Recommendation:** Option C - Add stub so the structure is in place.

### 5. Timeline for removal?

**Option A:** Remove in v1.2.0 (2 releases away)
**Option B:** Remove in v2.0.0 (major version bump)
**Option C:** Never remove (permanent deprecation)

**Recommendation:** Option A - v1.2.0 gives 2 releases (4-8 weeks) for users to migrate.

---

## 8. Success Criteria

### Phase 1 Success (Unified Command Working)

- [ ] All `/popkit:account` subcommands functional
- [ ] 100% feature parity with old commands
- [ ] Zero breaking changes for users
- [ ] All tests passing

### Phase 2 Success (Deprecation Warnings Active)

- [ ] Users see clear deprecation warnings
- [ ] Migration guide published
- [ ] Documentation updated
- [ ] No user confusion about which command to use

### Phase 3 Success (Removal Complete)

- [ ] Old commands removed cleanly
- [ ] No broken references in docs
- [ ] User migration complete (based on telemetry if available)
- [ ] Positive user feedback on simplification

---

## 9. Risk Assessment

### Low Risk

- ✅ Backward compatibility maintained during migration
- ✅ Clear deprecation timeline (2+ releases)
- ✅ No data loss or config changes
- ✅ All functionality preserved

### Medium Risk

- ⚠️ Users may not notice deprecation warnings
- ⚠️ Documentation updates could miss some files
- ⚠️ External tutorials/blogs may reference old commands

**Mitigation:**
- Make deprecation warnings VERY visible
- Comprehensive documentation search
- Add migration guide to release notes

### High Risk

- ❌ None identified

---

## 10. Appendix

### Command Comparison Matrix

| Capability | Before | After |
|------------|--------|-------|
| View account status | `/popkit:account` or `/popkit:cloud status` | `/popkit:account` |
| Create account | `/popkit:upgrade` or `/popkit:cloud signup` | `/popkit:account signup` |
| Login to account | `/popkit:cloud login` | `/popkit:account login` |
| Manage API keys | `/popkit:account keys` | `/popkit:account keys` |
| View usage stats | `/popkit:account usage` | `/popkit:account usage` |
| Logout | `/popkit:account logout` or `/popkit:cloud logout` | `/popkit:account logout` |
| **Total commands** | **3 commands** | **1 command** |

### File Structure

**Before:**
```
packages/popkit-core/commands/
├── account.md (status, usage, keys, logout)
├── upgrade.md (signup via browser)
└── cloud.md (signup, login, status, logout)

packages/popkit-core/skills/
└── pop-cloud-signup/ (actual signup implementation)
```

**After (Phase 1-2):**
```
packages/popkit-core/commands/
├── account.md (all 6 subcommands)
├── upgrade.md (deprecated, redirects to account)
└── cloud.md (deprecated, redirects to account)

packages/popkit-core/skills/
└── pop-cloud-signup/ (unchanged, used by account signup)
```

**After (Phase 3):**
```
packages/popkit-core/commands/
└── account.md (all 6 subcommands)

packages/popkit-core/skills/
└── pop-cloud-signup/ (unchanged)
```

---

## Next Steps

1. **Review this plan** - Validate approach and timeline
2. **Create GitHub issue** - Track implementation as Epic
3. **Break into sub-issues:**
   - Issue 1: Create unified `/popkit:account` command
   - Issue 2: Add deprecation warnings
   - Issue 3: Update documentation
   - Issue 4: Remove deprecated commands (future release)
4. **Begin implementation** - Start with Phase 1 (Week 1)

---

**End of Plan**
