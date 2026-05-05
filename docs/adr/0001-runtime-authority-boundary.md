# Runtime authority belongs inside explicit workflows

PopKit may observe, preload context, validate danger, and offer lightweight guidance across a coding session, but it should only take strong control after the user starts an explicit workflow. This keeps PopKit from becoming hidden always-on automation while preserving the original goal: deterministic building blocks should guide development work when the user intentionally enters a PopKit workflow.

Explicit workflows must publish provider-neutral workflow activity state so users can tell when PopKit is running, waiting, blocked, or complete. Claude Code can render that state through its status line; other providers can render it through their own UI, transcript output, MCP resources, or plain text.

**Considered Options**

- Always-on autopilot: rejected because it makes ordinary AI interactions feel opaque and heavy.
- Explicit workflow authority: accepted because it keeps PopKit visible, bounded, and easier to trust.

**Consequences**

- Workflows should expose visible progress or an active indicator when PopKit is in control.
- Global hooks should avoid hidden multi-step work, file mutation, agent spawning, or forced decision loops.
- The activity state contract should be provider-neutral; status lines are only one rendering.
