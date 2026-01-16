# AI Coding Tool Capabilities Matrix

**Last Updated:** December 2025
**Purpose:** Document capabilities of major AI coding tools to inform PopKit's multi-model expansion

## Overview

This document analyzes 6 major AI coding tools to identify:

1. Common capabilities (features PopKit can leverage across all tools)
2. Unique capabilities (tool-specific features)
3. Integration opportunities (how PopKit can add value)
4. MCP support status (critical for Universal MCP Server epic)

---

## Tools Analyzed

| Tool                                                  | Company          | Type                        | MCP Support  |
| ----------------------------------------------------- | ---------------- | --------------------------- | ------------ |
| [Claude Code](https://claude.ai/code)                 | Anthropic        | CLI + Plugins               | Native       |
| [Cursor](https://cursor.com)                          | Cursor Inc       | Fork of VS Code             | Native       |
| [Continue.dev](https://continue.dev)                  | Continue         | VS Code/JetBrains Extension | Full Support |
| [Windsurf](https://windsurf.com)                      | Codeium          | Standalone IDE              | Unknown      |
| [GitHub Copilot](https://github.com/features/copilot) | GitHub/Microsoft | Extension (multi-IDE)       | Partial      |
| [Gemini Code Assist](https://codeassist.google)       | Google           | Extension (multi-IDE)       | Unknown      |

---

## Feature Comparison Matrix

### Core Coding Features

| Feature                | Claude Code | Cursor | Continue | Windsurf               | Copilot     | Gemini      |
| ---------------------- | ----------- | ------ | -------- | ---------------------- | ----------- | ----------- |
| Code Completion        | Via tools   | Native | Native   | Native (Supercomplete) | Native      | Native      |
| Chat Interface         | Yes         | Yes    | Yes      | Yes (Cascade)          | Yes         | Yes         |
| Multi-file Editing     | Yes         | Yes    | Yes      | Yes                    | Yes (Agent) | Yes (Agent) |
| Codebase Understanding | Deep        | Deep   | Deep     | Deep (RAG)             | Deep        | Deep        |
| Terminal Integration   | Full        | Full   | Partial  | Yes                    | Full        | Partial     |
| Web Search             | Yes         | Yes    | Limited  | Yes                    | Yes         | Yes         |
| Image Understanding    | Yes         | Yes    | Limited  | Yes                    | Yes         | Yes         |

### Agent Capabilities

| Feature          | Claude Code   | Cursor           | Continue | Windsurf     | Copilot       | Gemini  |
| ---------------- | ------------- | ---------------- | -------- | ------------ | ------------- | ------- |
| Agent Mode       | Via Task tool | Yes (8 parallel) | Yes      | Cascade Flow | Yes           | Yes     |
| Background Tasks | Yes           | Yes (worktrees)  | Limited  | Unknown      | Yes (Actions) | Unknown |
| Plan Mode        | Yes           | Yes              | Unknown  | Via Cascade  | Yes           | Yes     |
| Self-Correction  | Yes           | Yes              | Yes      | Yes          | Yes           | Yes     |
| Tool Calling     | Native        | Native           | Via MCP  | Unknown      | Native        | Native  |

### MCP Integration

| Feature            | Claude Code | Cursor     | Continue   | Windsurf | Copilot | Gemini  |
| ------------------ | ----------- | ---------- | ---------- | -------- | ------- | ------- |
| MCP Client         | Yes         | Yes        | Full       | Unknown  | Partial | Unknown |
| MCP Server Hosting | Via plugins | Via config | Via config | Unknown  | Unknown | Unknown |
| Resources Support  | Yes         | Yes        | Yes        | Unknown  | Unknown | Unknown |
| Tools Support      | Yes         | Yes        | Yes        | Unknown  | Unknown | Unknown |
| Prompts Support    | Yes         | Yes        | Yes        | Unknown  | Unknown | Unknown |
| Sampling Support   | Yes         | Yes        | Yes        | Unknown  | Unknown | Unknown |

### Extensibility

| Feature         | Claude Code  | Cursor    | Continue     | Windsurf   | Copilot                  | Gemini          |
| --------------- | ------------ | --------- | ------------ | ---------- | ------------------------ | --------------- |
| Plugin System   | Yes (rich)   | Rules/MCP | MCP + Config | Extensions | Extensions               | Custom Commands |
| Custom Commands | Yes (skills) | Rules     | Yes          | Unknown    | .copilot-instructions.md | Rules           |
| Hooks System    | Yes (Python) | Limited   | Unknown      | Unknown    | Unknown                  | Unknown         |
| Output Styles   | Yes          | No        | No           | No         | No                       | No              |
| Agents          | Yes (30+)    | No        | No           | No         | No                       | No              |

---

## Tool Deep Dives

### Claude Code

**Strengths:**

- Rich plugin ecosystem (commands, skills, agents, hooks)
- Native MCP support as both client and server host
- Extended thinking with token budgets
- Background task orchestration
- PDF/image processing

**Unique Features:**

- Hooks system for automation (pre/post tool use)
- Output styles for consistent formatting
- Agent routing based on context
- Power Mode for multi-agent coordination

**PopKit Integration:** Native - PopKit IS a Claude Code plugin

---

### Cursor

**Strengths:**

- VS Code fork with deep AI integration
- 8 parallel agents using git worktrees
- AI Code Reviews built-in
- Debug Mode with runtime instrumentation
- Instant Grep for all models

**Unique Features:**

- Bugbot for source control integration
- Preconfigured MCP handlers
- Interpolated variables in MCP config

**PopKit Integration Opportunity:**

- MCP server exposing PopKit tools
- Pattern sharing across Cursor projects
- Workflow tracking via MCP

---

### Continue.dev

**Strengths:**

- First full MCP support for all features
- Open source and model-agnostic
- Docker + Continue Hub integration
- Works in VS Code and JetBrains

**Unique Features:**

- Can import MCP configs from Claude Desktop, Cursor, Cline
- Hub for discovering MCP servers
- First-class remote server support

**PopKit Integration Opportunity:**

- MCP server in Continue Hub
- Seamless config import from Claude Code
- Cross-IDE workflow continuity

---

### Windsurf (Codeium)

**Strengths:**

- Purpose-built AI IDE (not a fork)
- Cascade agent for deep codebase understanding
- Supercomplete predicts entire functions
- Focus on "flow state" for developers
- Free for individuals

**Unique Features:**

- RAG-based semantic indexing
- Image-to-code conversion
- In-editor live previews
- Write Mode vs Chat Mode

**PopKit Integration Opportunity:**

- If MCP supported: Full integration via Universal MCP Server
- If not: Custom Codeium extension or API integration

**Research Needed:** Verify MCP support status

---

### GitHub Copilot

**Strengths:**

- Largest user base
- Enterprise-ready with GitHub integration
- GPT-5-Codex and GPT-5.1-Codex-Max models
- Async coding agent with GitHub Actions
- Available in VS Code, JetBrains, Eclipse, Xcode

**Unique Features:**

- Assign issues directly to Copilot
- Ephemeral dev environments via Actions
- Context-isolated sub-agents
- Agent-specific instructions (.instructions.md)

**PopKit Integration Opportunity:**

- MCP adoption by OpenAI in 2025 enables integration
- Workflow tracking could complement Copilot agent
- Pattern sharing across Copilot users

---

### Gemini Code Assist

**Strengths:**

- Free tier with generous limits (6,000 code + 240 chat/day)
- Gemini 2.5 Pro/Flash models
- Agent Mode for multi-file tasks
- Custom commands and rules
- Next Edit Predictions

**Unique Features:**

- Thinking insights (shows reasoning process)
- Source citations in responses
- Clickable filenames in chat
- Rules for project conventions

**PopKit Integration Opportunity:**

- If MCP supported: Full integration
- If not: Potential for Google-specific adapter

**Research Needed:** Verify MCP support status

---

## Common Capabilities (Universal PopKit Value)

Features PopKit can provide across ALL tools:

| Capability            | PopKit Implementation                       |
| --------------------- | ------------------------------------------- |
| **Workflow Tracking** | Start/checkpoint/complete workflows         |
| **Pattern Database**  | Cross-project pattern search and submission |
| **Memory/Learning**   | Recall learnings from previous sessions     |
| **Coordination**      | Power Mode lite for multi-agent work        |
| **Quality Gates**     | TypeScript/lint/test validation             |
| **Session State**     | Save/restore development context            |

---

## MCP Tool Design

Based on this analysis, the Universal MCP Server should expose:

### Core Tools (All Platforms)

```typescript
// Workflow Management
popkit_workflow_start(goal: string): WorkflowId
popkit_workflow_checkpoint(id: WorkflowId, state: object): void
popkit_workflow_complete(id: WorkflowId, outcome: object): void

// Pattern Database
popkit_pattern_search(query: string, limit?: number): Pattern[]
popkit_pattern_submit(pattern: Pattern): PatternId
popkit_pattern_vote(id: PatternId, vote: 'up' | 'down'): void

// Memory/Learning
popkit_memory_recall(query: string): Memory[]
popkit_memory_store(key: string, value: object): void

// Coordination
popkit_agent_checkin(state: AgentState): void
popkit_agent_barrier(phase: string): void
popkit_agent_broadcast(message: object): void

// Quality
popkit_quality_check(checks: string[]): QualityResult
popkit_health_status(): HealthReport
```

### Platform-Specific Adaptations

| Platform    | Adaptation                              |
| ----------- | --------------------------------------- |
| Claude Code | Native plugin (current)                 |
| Cursor      | MCP config in .cursor/mcp.json          |
| Continue    | MCP config + Hub listing                |
| Windsurf    | TBD - research MCP support              |
| Copilot     | MCP config (OpenAI adopted MCP in 2025) |
| Gemini      | TBD - research MCP support              |

---

## Next Steps

1. **Verify MCP support** for Windsurf and Gemini Code Assist
2. **Design API contracts** for model-agnostic cloud endpoints
3. **Implement Universal MCP Server** (Issue #112)
4. **Create setup guides** for each platform
5. **Build test suite** for cross-platform validation

---

## Sources

- [Cursor Changelog](https://cursor.com/changelog)
- [Cursor MCP Guide](https://steveshao.com/posts/2025/note-use-mcp-for-cursor/)
- [Continue MCP Documentation](https://docs.continue.dev/customize/deep-dives/mcp)
- [MCP Anniversary Blog](http://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/)
- [Windsurf IDE Review](https://medium.com/@urano10/windsurf-ide-review-2025-the-ai-native-low-code-coding-environment-formerly-codeium-335093f5619b)
- [GitHub Copilot Features](https://docs.github.com/en/copilot/get-started/features)
- [Copilot Coding Agent Docs](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent)
- [Gemini Code Assist Overview](https://developers.google.com/gemini-code-assist/docs/overview)
- [Gemini Code Assist Agent Mode](https://blog.google/technology/developers/gemini-code-assist-updates-july-2025/)

---

_This document is part of PopKit's Multi-Model Foundation epic (#111)_
