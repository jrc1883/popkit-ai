# Agent SDK v2 Integration Analysis

**Date**: December 9, 2025
**Context**: Analysis of new Claude Agent SDK features (1M context, sandboxing, TypeScript V2) for PopKit integration

---

## Executive Summary

Three major features were shipped with the latest Claude Agent SDK updates that create significant opportunities for PopKit:

1. **1M Context Windows** - enables full-codebase processing without RAG
2. **Sandboxing** - OS-level isolation with granular tool control
3. **TypeScript V2 Interface** - breaking changes requiring migration

**Key Insight**: Together, these enable PopKit to become a **full-stack orchestrator** with persistent multi-agent workflows, isolated execution environments, and complete project context.

---

## Feature Analysis

### 1. 1M Context Windows (Public Beta)

#### What It Enables
- **750,000+ words** or **75,000+ lines of code** in a single request
- **100% accuracy** in needle-in-haystack retrieval across full context
- 5x increase from previous 200K limit

#### PopKit Integration Opportunities

**Immediate (High Priority)**
- **Tier 1 Agent Enhancement**: Code-reviewer, code-explorer agents now have full project visibility
  - Eliminates need for selective file loading; can include entire codebase in context
  - Enables holistic refactoring suggestions across 50+ files simultaneously

- **Project Context Synthesis**: The meta-agent can now load:
  - All source files + tests + documentation in one pass
  - Complete git history (100+ recent commits)
  - Configuration files, environment specs, dependency trees
  - Result: Better architectural understanding for code-architect

- **Large-Codebase Support**:
  - Monorepos (like PopKit itself) become analyzable end-to-end
  - Reduces "context fragmentation" where agents miss cross-module impacts

**Near-term (Medium Priority)**
- **Knowledge Distillation**: Session synthesis could now:
  - Process entire sprint's work (50+ PRs) in parallel
  - Generate cross-cutting insights unavailable from individual change review
  - Feed into `/popkit:routine` nightly summaries with full project coverage

- **Migration & Refactoring at Scale**:
  - migration-specialist agent can understand all affected locations
  - dead-code-eliminator can process entire codebase in single analysis pass

**Future (Lower Priority)**
- **Research-Grade Analysis**: researcher agent could digest:
  - Entire codebase + all documentation + research papers
  - Generate system design PRDs with comprehensive coverage

- **Power Mode Coordination**: Parallel agents can now share full project context without external storage
  - Reduces need for Redis message passing for context sharing
  - Agents can reason about side-effects across the full system

#### Constraints & Considerations
- Still in public beta (rolling out through Dec/early 2025)
- Applies to Sonnet 4.5 models (our tier-1 reasoning model)
- Requires explicit context-1m-2025-08-07 header in API calls
- Cost: Same per-token, but enables batch processing (50% additional savings available)

#### Recommended Action
**Enablement Phase**: Create an agent config flag `useLargeContext: true` for specific agents:
```json
{
  "agent": "code-reviewer",
  "model": "claude-sonnet-4-5",
  "largeContext": {
    "enabled": true,
    "maxTokens": 800000,
    "includeFiles": ["**/*.ts", "**/*.tsx", "**/*.md"],
    "excludePatterns": ["node_modules/**", "dist/**"]
  }
}
```

---

### 2. Sandboxing (Stable Feature)

#### What It Provides
- **Multi-layer isolation**: OS-level filesystem/network restrictions + optional container wrapping
- **Granular tool control**: Agents can be restricted to specific tools (Bash, Read, Edit, etc.)
- **Ephemeral filesystems**: Each agent execution starts clean; no pollution between runs

#### PopKit Integration Opportunities

**Immediate (High Priority)**
- **Tier 2 Agent Isolation**: High-risk agents now safely isolatable:
  - devops-automator: Can make actual cloud API calls without risk to production
  - deployment-validator: Can run real deployment validation without side effects
  - rapid-prototyper: Can execute arbitrary code in isolated environment

- **Tool Restrictions by Agent Role**:
  - **Code reviewers**: `tools: ['Read']` - read-only analysis, no execution
  - **Bug reproducers**: `tools: ['Bash', 'Read', 'Edit']` - controlled experimentation
  - **Architects**: `tools: ['Read', 'Bash']` - static analysis + build verification
  - **Dead-code-eliminator**: `tools: ['Read', 'Edit']` - structured changes only

**Near-term (Medium Priority)**
- **Workspace Isolation for Parallel Agents**:
  - Power Mode agents (6+ running in parallel) isolated from each other
  - Each agent has own ephemeral filesystem → no race conditions
  - Coordinator can execute agents concurrently without mutex locks

- **Multi-Tenant Project Support** (Future Platform):
  - Different users' agents run in separate sandboxes
  - Cloud backend can safely execute user-submitted agent code

**Future (Lower Priority)**
- **Controlled External Integrations**:
  - Agents can connect to specific APIs only (GitHub, Slack, etc.)
  - Network isolation prevents exfiltration of credentials
  - Audit log of all external API calls

#### Constraints & Considerations
- Linux-only for native OS-level isolation (production-grade)
- Docker/gVisor/Firecracker for enhanced security in cloud deployments
- `enableWeakerNestedSandbox: true` needed for Docker environments
- Performance: ~5-10ms overhead per sandbox setup

#### Recommended Action
**Safety-First Rollout**: Start with read-only agents:
```json
{
  "agent": "code-reviewer",
  "sandbox": {
    "enabled": true,
    "tools": ["Read"],
    "filesystem": {
      "readOnly": ["${workspaceFolder}"]
    }
  }
}
```

Escalate to execution agents after validation.

---

### 3. TypeScript V2 Interface (Breaking Change)

#### Major Breaking Changes
1. **System Prompt**: Single `systemPrompt` field (not separate `customSystemPrompt`/`appendSystemPrompt`)
2. **Filesystem Auto-Loading Disabled**: Nothing loads from filesystem by default
   - Must explicitly specify `settingSources: ["user", "project", "local"]`
   - Prevents unexpected behavior from CLAUDE.md, slash commands, subagents in filesystem
3. **Programmatic Subagents**: Agents can now be defined inline instead of filesystem-only
4. **Session Forking**: New `forkSession()` API for branching conversations
5. **Package Import**: `claude-agent-sdk` (not `claude-code`)

#### PopKit Integration Opportunities

**Immediate (High Priority)**
- **Tier 1 Agent Rewrite**: Migrate all 11 core agents to V2 API
  - Consolidate system prompts for consistency
  - Explicit tool allowlisting per agent
  - Inline agent definitions for reproducibility

- **Cloud Platform Ready**: V2's programmatic agent definition enables:
  - API-generated agents (cloud backend creates custom agents on-demand)
  - No filesystem dependencies = easier cloud deployment
  - Agents can be versioned & A/B tested via API

**Near-term (Medium Priority)**
- **Session Forking Feature**: Implement decision trees via `/popkit:explore-branch`
  ```
  User: "Should I refactor this or rewrite it?"
  → Creates fork 1: Code-reviewer analyzes refactoring path
  → Creates fork 2: Code-architect analyzes rewrite path
  → Compare recommendations
  ```

- **Explicit Configuration Safety**:
  - Removes "magic" loading of CLAUDE.md/slash commands
  - Makes agent behavior predictable and auditable
  - Important for compliance/reproducible workflows

**Future (Lower Priority)**
- **Multi-Model Orchestration**: V2 API enables mixing models:
  - Haiku for fast screening
  - Sonnet for detailed analysis
  - Opus for complex architecture decisions
  - All composable in single workflow

#### Migration Path
1. **Phase 1** (Dec 2025): Migrate core Tier 1 agents (11 agents)
2. **Phase 2** (Jan 2026): Migrate Tier 2 agents (17 agents)
3. **Phase 3** (Feb 2026): Migrate feature-workflow agents (3 agents)
4. **Phase 4** (Mar 2026): Update MCP server generation template to V2

---

## Integration Priorities & Timeline

### Immediate (Next 2 Weeks)
**1M Context Integration + Sandboxing Setup**
- [ ] Enable 1M context for code-reviewer (test on medium-sized repo)
- [ ] Add sandbox configuration to agent config schema
- [ ] Implement tool restriction patterns for Tier 1 agents
- **Impact**: Code review quality + agent isolation

### Near-term (1 Month)
**TypeScript V2 Migration Start + Power Mode Optimization**
- [ ] Migrate 3-5 core Tier 1 agents to V2 API
- [ ] Update MCP server template to V2
- [ ] Implement session forking for code-architect decision trees
- **Impact**: Future-proof platform + new explore-branch capability

### Medium-term (2-3 Months)
**Full V2 Migration + Large Context Scaling**
- [ ] Complete migration of all 31 agents to V2
- [ ] Roll out 1M context to all Tier 1 agents
- [ ] Implement cross-agent context sharing via 1M window
- **Impact**: Unified architecture + enterprise-ready system

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| V2 breaking changes break existing workflows | Start with non-critical agents; extensive testing before rollout |
| 1M context increases latency | Use for specific agent roles only (reviewers, architects); batch processing |
| Sandbox overhead impacts performance | Monitor; use selectively for high-risk agents first |
| Users on older Claude Code versions can't use V2 features | Document requirements; auto-detect and graceful degrade |

---

## Strategic Implications

**Before**: PopKit was a sophisticated plugin orchestrator with smart routing and stateless hooks.

**After**: PopKit becomes:
1. **Full-codebase analyzer** (1M context)
2. **Safely executable** (sandboxing with tool control)
3. **Cloud-native platform** (V2 API, programmatic agents)
4. **Multi-session capable** (forking for decision trees)

This positions PopKit for:
- **Enterprise adoption** (security via sandboxing, full audit trails)
- **Multi-model orchestration** (V2 enables Claude + Sonnet + Opus mixing)
- **Standalone platform** (APIs + cloud backend enables non-plugin deployments)

---

## Next Steps

1. **Research Phase Complete** ✅
2. **Implementation Planning**: Design agent config schema extensions for 1M context + sandboxing
3. **Pilot Implementation**: Migrate 2-3 agents to demonstrate patterns
4. **Validation**: Test on PopKit's own codebase (recursive dogfooding)
5. **Documentation**: Create migration guide for all 31 agents

---

## References

- [Claude 1M Context Announcement](https://www.anthropic.com/news/1m-context)
- [Agent SDK Sandboxing Guide](https://code.claude.com/docs/en/sandboxing)
- [TypeScript V2 Migration Guide](https://docs.claude.com/en/docs/claude-code/sdk/migration-guide)
- [Agent SDK GitHub Repo](https://github.com/anthropics/claude-agent-sdk-typescript)
