# PopKit Workflow Audit Findings

**Date:** 2025-12-19
**Session:** PopKit Workflow Optimization

## Summary

Completed audit of morning/nightly routine workflows to identify optimization opportunities and best practices alignment.

## Key Findings

### 1. Current State - COMPLETE Implementation

**Routine System:**
- Unified command structure in `packages/plugin/commands/routine.md` (382 lines)
- Both morning and nightly routines fully specified
- Universal `pk` routine + project-specific slot system
- Premium generator skills for custom routines

**Files:**
- `commands/routine.md` - Main command specification
- `skills/pop-morning-generator/SKILL.md` - Morning routine generator (493 lines)
- `skills/pop-nightly-generator/SKILL.md` - Nightly routine generator (462 lines)
- `docs/plans/2025-12-03-unified-routine-management.md` - Implementation plan (approved)

### 2. Terminology Clarification Needed

Current confusion between:
- **PopKit Project** - Single codebase using PopKit
- **Workspace** - Undefined (monorepo? multi-project?)
- **Universal Routine** - Built-in `pk` routine
- **Generic Routine** - Issues #488, #498 (workspace templates)
- **Custom Routine** - Project-specific (Pro tier)

### 3. Context Efficiency Opportunities

**Documentation Size:**
- `routine.md`: 382 lines (repetitive examples)
- `morning-generator/SKILL.md`: 493 lines (verbose templates)
- `nightly-generator/SKILL.md`: 462 lines (duplicate content)

**Recommendation:** Extract templates to `packages/plugin/templates/routines/`

Estimated savings: 30-40% reduction

### 4. Best Practices Gaps

| Practice | Status | Action |
|----------|--------|--------|
| Spec-driven | Partial | Add JSON schema for routine config |
| Async agents | Missing | Use Task tool for parallel checks |
| Benchmarking | Missing | Add timing metrics to output |
| Testing | Missing | Create routine test fixtures |

### 5. Issues #488 & #498 Clarification

These issues are for **generic workspace templates**, NOT project-specific routines.

**Distinction:**
- Universal `pk` routine = Works on PopKit projects
- Generic workspace = Works on ANY project (no PopKit config)

## Next Steps

### Phase 1: Documentation
1. Add terminology section to CLAUDE.md
2. Define project vs workspace clearly
3. Optimize routine documentation size

### Phase 2: Complete Generic Templates
1. Issue #488 - Generic morning template
2. Issue #498 - Generic nightly template

### Phase 3: Best Practices
1. JSON schema validation
2. Async agent integration
3. Benchmarking and metrics
4. Test framework

## Notes

- Session interrupted by display bug in Claude Code
- All findings documented for continuation
- Ready to proceed with any of the three phases
