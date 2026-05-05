# PopKit

PopKit is a provider-agnostic workflow runtime for AI-assisted software development. It exists to make repeatable development work portable across AI coding hosts without making the host itself the product.

## Language

**Workflow**: A user-facing development job that PopKit helps complete from intent to recommendation or handoff.
_Avoid_: Tool, command, script

**Advisory Workflow**: A workflow that analyzes context and recommends a next move without necessarily changing project state.
_Avoid_: Report, suggestion, dashboard

**Execution Workflow**: A workflow that performs project work and must end with a reviewable handoff.
_Avoid_: Task run, automation, agent swarm

**Handoff**: The reviewable result of completed or blocked execution work.
_Avoid_: Summary, output, report

**Next-Step Options**: Explicit follow-up choices produced at the end of a workflow.
_Avoid_: AskUserQuestion, plan mode, generic advice

**Decision Point**: A moment in a workflow where PopKit narrows ambiguity into a small set of defensible choices.
_Avoid_: Branch, prompt, vague judgment call

**Option Set**: The bounded choices PopKit presents at a decision point.
_Avoid_: Ideas, possibilities, myriad options

**Decision Batch**: A grouped set of related decision points presented together so the user can answer once before execution continues.
_Avoid_: Wizard, survey, repeated prompts

**Profile Proposal**: A recommended project profile or workflow configuration generated from detected facts and presented for approval or edits.
_Avoid_: Wizard, auto-config, template

**Expertise Source**: A built-in or external skill, agent, rubric, routine, or domain method that can inform a workflow.
_Avoid_: PopKit opinion, generic best practice, model knowledge

**Expertise Registry**: The curated list of expertise sources that PopKit is allowed to route to.
_Avoid_: Search index, marketplace, arbitrary discovery

**Runtime Authority**: The degree to which PopKit controls the session flow instead of only observing or advising.
_Avoid_: Autopilot, background magic, hidden control

**Active Workflow Indicator**: A visible signal that a PopKit workflow is running or has just produced a decision.
_Avoid_: Hook response, status line, log entry

**Workflow Activity State**: Provider-neutral workflow state that can be rendered through an active workflow indicator.
_Avoid_: UI status, hook event, progress log

**Project Profile**: PopKit's structured understanding of a project's stack, risk areas, routine checks, workflows, and relevant expertise.
_Avoid_: Template, generic project type, knowledge graph

**Project-Tuned Workflow**: A workflow customized from a project profile instead of copied from a default template.
_Avoid_: Template, one-off script, generic routine

**Project Initialization**: The setup workflow that establishes PopKit configuration, onboarding choices, project profile defaults, and next-step direction for a project.
_Avoid_: Profile setup, routine generation, install

**Project Adoption**: The workflow that safely connects PopKit to an existing project and proposes profile, routine, and workflow updates without treating the project as new.
_Avoid_: Re-initialization, migration, install

**Local Project State**: Project-local PopKit files that store approved configuration, routines, profiles, workflow state, and coordination artifacts.
_Avoid_: Global install, cloud state, hidden magic

**Coordination Plane**: An optional shared runtime surface where agents, providers, or workflows exchange jobs, claims, events, and results.
_Avoid_: PopKit install, project adoption, always-on service

**Multi-Agent Coordination**: A workflow pattern where multiple agents or providers divide, review, claim, and hand off related work through visible coordination records.
_Avoid_: Power Mode, agent swarm, hidden autopilot

**Legacy Power Mode**: The existing PopKit implementation label for multi-agent coordination features.
_Avoid_: Domain term, product category, user-facing requirement

**Coordination Job**: A unit of work published to a coordination plane for an agent or provider to claim.
_Avoid_: GitHub issue, workflow, task message

**Work Claim**: A visible record that an agent or provider has claimed a coordination job.
_Avoid_: Assignment, lock, hidden state

**Installation**: The machine or provider setup that makes PopKit available before any specific project is configured.
_Avoid_: Project adoption, initialization, MCP server runtime

**Runtime**: The product layer that preloads context, invokes deterministic building blocks, and coordinates workflows across providers.
_Avoid_: Framework, app shell, coding-tool fork

**Provider**: An AI coding host or integration target where PopKit workflows can run.
_Avoid_: Model vendor, cloud provider, runtime

**Skill**: A small, repeatable, preferably programmatic building block that a workflow may invoke.
_Avoid_: Plugin, prompt, command

**Lifecycle Hook**: A provider-triggered event point where PopKit can gather context, validate behavior, or guide the next step.
_Avoid_: Skill, workflow, command

**Command**: A stable user-facing entry point that starts a workflow or invokes a skill directly.
_Avoid_: Skill, hook, runtime

**Interaction Surface**: The host-owned UI channel used to present decisions or next-step choices to the user.
_Avoid_: Skill, AskUserQuestion, plan mode

**MCP server**: A delivery surface for exposing PopKit capabilities to compatible providers.
_Avoid_: Product, runtime, workflow

## Relationships

- A **Workflow** may compose one or more **Skills**, **Lifecycle Hooks**, and provider-neutral scripts.
- An **Advisory Workflow** is a **Workflow** that may stop at a recommendation.
- An **Execution Workflow** is a **Workflow** that produces a **Handoff**.
- Every **Workflow** ends with **Next-Step Options**.
- The **Runtime** coordinates **Workflows** across one or more **Providers**.
- **Runtime Authority** is strong inside an explicit **Workflow** and light outside one.
- A **Command** is how a user usually starts a **Workflow**.
- An **Interaction Surface** renders **Next-Step Options**, but the host chooses the surface.
- Every explicit **Workflow** publishes **Workflow Activity State**.
- An **Active Workflow Indicator** renders **Workflow Activity State** to make **Runtime Authority** visible.
- A **Workflow** may include **Decision Points** with bounded **Option Sets**.
- Related **Decision Points** should be grouped into a **Decision Batch** when answers can be collected before execution.
- A **Workflow** may route to one or more **Expertise Sources**.
- The **Runtime** routes through an **Expertise Registry**, not arbitrary dynamic discovery.
- A **Project Profile** informs routine checks, next-action recommendations, project-tuned workflows, and expertise routing.
- A **Project-Tuned Workflow** is created or adapted from a **Project Profile**.
- **Project Initialization** may produce a **Profile Proposal** as part of setup.
- A **Profile Proposal** groups recommended defaults into **Decision Batches** for approval or edits.
- **Project Adoption** is the existing-project counterpart to **Project Initialization**.
- **Installation** makes PopKit available; **Project Initialization** and **Project Adoption** configure PopKit for a specific project.
- **Project Adoption** may write **Local Project State** after the user approves a profile proposal.
- A **Coordination Plane** is optional and is used for cross-provider or multi-agent coordination, not ordinary installation or adoption.
- **Multi-Agent Coordination** may use a **Coordination Plane**.
- **Legacy Power Mode** is an existing implementation label for parts of **Multi-Agent Coordination**.
- Agents publish and claim **Coordination Jobs** through **Work Claims** when shared coordination is enabled.
- An **MCP server** exposes **Runtime** capabilities to compatible **Providers**.

## Example Dialogue

> **Dev:** "Should we describe PopKit as another coding tool?"
> **Domain expert:** "No. PopKit is a **Runtime** for **Workflows** that can run through multiple **Providers**. Forking a coding tool could become a **Provider** strategy later, but it is not the current product identity."

## Flagged Ambiguities

- "Provider-agnostic" can mean model-vendor independence or coding-host independence; resolved: in PopKit, a **Provider** is an AI coding host or integration target.
- "Forking PyCoder/OpenCode into PopKit" is an optional future product path, not the current definition of the **Runtime**.
- "PopKit as a custom coding host" is not a current product direction; resolved: host forks remain outside the core unless a specific **Workflow** cannot be made reliable through existing **Providers**.
- "Skill" and "Workflow" can blur because skills can contain internal recipes; resolved: a **Skill** is the building block, while a **Workflow** owns the user-facing job.
- "Always ask the user a question" is provider-specific; resolved: every **Workflow** must emit **Next-Step Options**, and the **Interaction Surface** decides whether those options are rendered as a blocking question or plain text.
- "Always-on PopKit control" is too heavy for ordinary AI interactions; resolved: PopKit may observe and lightly guide globally, but authoritative chaining, mutation, delegation, and workflow gating belong inside explicit **Workflows**.
- "Status line" is a provider-specific implementation; resolved: the domain need is an **Active Workflow Indicator**, which Claude Code can render through a status line while other providers may use different surfaces.
- "Workflow visibility" is required, not optional; resolved: every explicit **Workflow** must publish **Workflow Activity State** now, even if some providers initially render it as plain text.
- "AI judgment" should not expand into unbounded options; resolved: PopKit should use **Decision Points** and **Option Sets** to constrain ambiguity while leaving final synthesis and tradeoff reasoning to the AI and user.
- "Human in the loop" should not mean repeated serial prompts; resolved: PopKit should front-load related decisions into **Decision Batches** with recommended defaults when practical.
- "PopKit expertise" is not assumed to be complete; resolved: PopKit can route to external **Expertise Sources** when a workflow needs knowledge outside PopKit's built-in development expertise.
- "External skills" are not discovered arbitrarily; resolved: PopKit is curated by default and open by registration through an **Expertise Registry**.
- "Playbook" is not a first-class PopKit term yet; resolved: use **Workflow** for the user-facing process and **Expertise Source** for reusable methods until a concrete implementation needs a separate noun.
- "Project customization" is not just templating; resolved: PopKit should maintain a **Project Profile** and use it to create **Project-Tuned Workflows**.
- "Project Profile" fields can be inferred, recommended, or confirmed; resolved: inferred fields may guide recommendations, but workflow-driving fields should be shown with recommended defaults and confirmed in batches before they become authoritative.
- "Project setup" is broader than profile setup; resolved: **Project Initialization** is the larger workflow, and **Profile Proposal** is the preferred interaction model for profile-driving defaults inside it.
- "Existing projects" should not be forced through new-project setup; resolved: PopKit needs **Project Adoption** for already-built repositories that want PopKit profile, routine, and workflow tuning.
- "Installing PopKit" is not the same as configuring a repository; resolved: **Installation** is separate from **Project Initialization** and **Project Adoption**.
- "Hidden local files" are acceptable after approval; resolved: project-specific behavior should live in **Local Project State**, but **Project Adoption** should start read-only and propose writes before creating or changing files.
- "Upstash-backed orchestration" is not the default project setup; resolved: cloud/shared infrastructure belongs behind an optional **Coordination Plane** for cross-provider or multi-agent workflows.
- "Power Mode" is not a clear canonical product term; resolved: use **Multi-Agent Coordination** for the domain concept and treat **Legacy Power Mode** as the existing implementation label until it is renamed, retired, or intentionally redefined.
