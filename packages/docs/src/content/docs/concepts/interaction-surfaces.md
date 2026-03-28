---
title: Interaction Surfaces
description: How PopKit chooses between plan UI, AskUserQuestion, and plain text
---

# Interaction Surfaces

An interaction surface is the UI channel PopKit uses when it needs the user to
choose between multiple next steps.

PopKit now treats that surface as a runtime capability chosen by the host before
the session starts. Commands and skills can emit provider-neutral decision data,
but they do not decide how that data is rendered.

## Hard Boundary

There is one boundary that matters for Codex and Genesis integrations:

- Skills cannot upgrade an already-running Codex session into plan mode
- The host launcher chooses the interaction surface before session start
- PopKit commands emit decision specs, then the host renders them through the
  best available surface

That means `/popkit-dev:next` can produce the same structured decision either
way, but the runtime decides whether the user sees `request_user_input`,
`AskUserQuestion`, or a plain-text fallback.

## Fallback Order

PopKit resolves interaction surfaces in this order:

1. `request_user_input` when the host explicitly says it is available
2. `AskUserQuestion` when the runtime supports PopKit interactive questions
3. Plain-text rendering when neither interactive surface is available

This keeps the command contract stable while letting each runtime expose the
best UX it actually supports.

## Decision Specs

Commands that support structured choices emit a provider-neutral decision spec.
The current pilot is `/popkit-dev:next`.

The spec includes:

- A stable header such as `Next Action`
- A plain-English question
- One to three ranked options
- A recommended option flag
- Exact follow-up commands for each option

The spec does not mention `request_user_input` or `AskUserQuestion` directly.
That keeps the payload reusable across Codex, Claude Code, and any future host.

## Pilot Flow For `/popkit-dev:next`

### Standard Codex Launch

```bash
popkit provider launch codex --mode default --command "/popkit-dev:next"
```

In this path, Codex runs with its normal interaction surface. `/popkit-dev:next`
still analyzes repository state, but the user sees the existing human-readable
report and runnable follow-up commands.

### Plan-Intent Codex Launch

```bash
POPKIT_HOST_CAN_REQUEST_USER_INPUT=1 \
popkit provider launch codex --mode plan --command "/popkit-dev:next"
```

In this path, the host declares that plan UI is available before Codex starts.
The launcher marks the session as `request_user_input` capable, and
`/popkit-dev:next` can be rendered as a structured decision prompt instead of
only a report.

If the host does not actually support plan UI, PopKit downgrades to the default
surface and prints a warning rather than pretending the skill can enable it.

## Genesis Example

For Genesis, the pragmatic integration is:

- Use PopKit `AskUserQuestion` when Genesis is running inside a Claude-style
  runtime that already supports it
- Use the host-owned Codex launch path when Genesis wants a plan-capable Codex
  session
- Fall back to the standard `/popkit-dev:next` report when neither interactive
  surface exists

That keeps the skill logic the same and moves the rendering choice to the part
of the system that actually owns the session.

## Related Commands

- `/popkit-dev:next` for the current pilot decision spec
- `/popkit-core:project init` for first-run onboarding and telemetry choices
- `popkit provider launch codex` for host-owned Codex launch selection
