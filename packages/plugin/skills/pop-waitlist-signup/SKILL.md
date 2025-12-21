---
name: pop-waitlist-signup
description: "[DEPRECATED] This skill is no longer used. API key enhancements are free - no waitlist needed. Use /popkit:cloud signup instead."
---

# Waitlist Signup Skill (DEPRECATED)

## ⚠️ Architecture Change Notice

**Status:** Deprecated as of December 20, 2025

This skill was designed for pre-launch waitlist collection for "premium features." PopKit's architecture has changed:

**Old Model (this skill):**
- Premium features launching soon
- Waitlist for paid tier access
- Email collection for launch notification

**New Model (API key enhancement):**
- All features free and available now
- API keys free (no waitlist needed)
- Enhancements, not premium features

## Migration

Instead of this skill, use:
- `/popkit:cloud signup` - Get free API key immediately
- `/popkit:upgrade` - Alternative signup flow
- No waitlist needed - everything is available

## Why Deprecated

1. **No premium features** - API key enhancements are free
2. **No launch event** - API keys available immediately
3. **No waitlist** - No reason to collect emails for future access

## For Historical Reference

This skill was part of Issue #353 (Premium Feature Gating) which implemented a subscription tier system. That architecture was replaced by the API key enhancement model (Epic #580) where:
- All workflows work locally (free)
- API key adds semantic intelligence (also free for now)
- No feature gating or tiers

## Related

- Epic #580 - PopKit Plugin Modularization
- Issue #581 - Update commands/skills to API key model
- Issue #353 - Premium Feature Gating (superseded)
- `pop-api-key-prompt` - Replacement skill for enhancement prompts

---

**Do not use this skill.** It references an architecture that no longer exists.

For API key signup, use `/popkit:cloud signup` instead.
