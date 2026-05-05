# External expertise is registered, not discovered arbitrarily

PopKit ships with curated development expertise, but it can route workflows to external expertise sources when the source is registered with domain, trigger phrases, non-goals, risk level, required tools, and execution capability. This keeps PopKit open to Matt Pocock-style skills, project-specific playbooks, or specialized domain methods without letting agents dynamically discover and trust arbitrary skills at runtime.

**Considered Options**

- Arbitrary discovery: rejected because it increases trust, safety, and consistency risk.
- Closed built-in expertise only: rejected because PopKit should not pretend to own every domain.
- Curated by default, open by registration: accepted because it preserves extensibility while keeping routing auditable.

**Consequences**

- High-stakes domains should default to advisory-only unless explicitly reviewed.
- Registered expertise needs enough metadata for routing, safety, and user explanation.
