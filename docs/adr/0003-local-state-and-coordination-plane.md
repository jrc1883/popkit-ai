# Project adoption writes local state; shared coordination is optional

Existing projects should not be treated as blank slates. Project adoption starts by reading the repository, generating a profile proposal, and asking for approval before writing project-local PopKit files. Approved project-specific behavior belongs in local project state so the repo remains inspectable and rerunnable.

Multi-agent or cross-provider coordination is a separate concern. PopKit may use a shared coordination plane, such as an Upstash-backed Redis/Workflow/Vector stack, for jobs, claims, events, and results, but that cloud surface is optional and must not be implied by installation or ordinary project adoption.

The existing "Power Mode" name is not the canonical domain language. Treat it as a legacy implementation label for some multi-agent coordination features until the product intentionally renames, retires, or redefines it.

**Considered Options**

- Write project-local files immediately: rejected because it feels invasive in existing repositories.
- Keep all project state global or cloud-hosted: rejected because project behavior becomes harder to inspect and review.
- Read-only first, then approved local writes, with optional shared coordination: accepted because it balances trust, auditability, and future multi-agent coordination.

**Consequences**

- Adoption must be diff-safe and rerunnable.
- Project-specific assumptions should live in local project state after approval.
- Shared coordination should have explicit opt-in, visible work claims, and clear ownership of jobs and results.
- Documentation and code should prefer "multi-agent coordination" for the domain concept and reserve "Power Mode" for legacy command paths while they exist.
