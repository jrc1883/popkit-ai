# "Power Mode" is legacy implementation language

The phrase "Power Mode" appears throughout the current repository, but it is not a clear canonical product or domain term. The underlying domain concept is multi-agent coordination: agents or providers divide work, claim jobs, review outputs, exchange events, and hand off results through visible coordination records.

Keeping "Power Mode" as the primary term makes the product harder to understand because future contributors cannot infer whether it means multi-agent execution, cloud coordination, background tasks, premium tiering, status widgets, or a specific Claude Code workflow. The term can remain as a backwards-compatible command or implementation label while the domain model uses "multi-agent coordination."

Repository history supports treating the term as accidental legacy language. In the current public history, it first appears as a 2025-11-29 multi-agent Redis/pub-sub orchestration feature, then quickly expands into file fallback, hosted cloud coordination, QStash messaging, Native Async, statusline widgets, and command routing. That expansion made the label less precise over time, not more precise.

**Considered Options**

- Keep Power Mode as the canonical term: rejected because the term is unclear even to the product owner.
- Delete Power Mode immediately: rejected because the current repo has many command, docs, hook, and schema references.
- Treat Power Mode as legacy language and use multi-agent coordination as the canonical domain term: accepted because it preserves compatibility while giving new work a clearer target.

**Consequences**

- New docs and planning should use "multi-agent coordination" unless referencing existing command paths.
- Existing `/popkit-core:power` surfaces can remain temporarily as compatibility aliases.
- Future cleanup should decide whether to rename, retire, or intentionally redefine the legacy Power Mode surface.
- Rename work should start with a coordination contract, not with a broad file-path sweep.
