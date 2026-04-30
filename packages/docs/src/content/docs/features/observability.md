---
title: Observability
description: Real-time monitoring of your Claude Code sessions
---

PopKit's observability feature gives you real-time visibility into what's happening in your Claude Code sessions. See agent activity, tool calls, and workflow progress as they happen.

## Dashboard

Access the observability dashboard at [popkit.unjoe.me/observe](https://popkit.unjoe.me/observe) (requires login).

The dashboard shows:

- **Activity Feed**: Real-time stream of events (tool calls, agent starts/ends, errors)
- **Active Agents**: Which agents are currently working
- **Tool Usage**: Most frequently used tools
- **Session Stats**: Today's totals for events, agent starts, and errors

## How It Works

1. Claude Code fires hook events (PreToolUse, PostToolUse, etc.)
2. The `agent-observability.py` hook captures these events
3. Events are sent to PopKit Cloud API
4. Dashboard receives events via SSE (Pro) or polling (Free)

```
Claude Code → Hook → PopKit Cloud API → Dashboard
                          ↓
                    Redis Stream
```

## Setup

### 1. Get Your API Key

```bash
/popkit-core:account login
```

Or sign up at [popkit.unjoe.me/signup](https://popkit.unjoe.me/signup).

### 2. Set Environment Variable

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
export POPKIT_API_KEY=pk_live_your_key_here
```

### 3. Register the Hook

The observability hook is included in `popkit-core`. If you've installed PopKit, it's already available.

To verify it's active:

```bash
/popkit-core:plugin status
```

## Event Types

| Event            | Description              |
| ---------------- | ------------------------ |
| `agent_start`    | An agent was spawned     |
| `agent_end`      | An agent completed       |
| `tool_call`      | A tool was invoked       |
| `tool_result`    | A tool returned a result |
| `error`          | An error occurred        |
| `workflow_phase` | A workflow phase changed |

## Pro vs Free

| Feature          | Free         | Pro           |
| ---------------- | ------------ | ------------- |
| Event capture    | Yes          | Yes           |
| Dashboard access | Yes          | Yes           |
| Update method    | Polling (3s) | SSE streaming |
| Event history    | Last 50      | Last 1000     |
| Stats retention  | Today only   | 7 days        |

## Troubleshooting

### Events Not Appearing

1. **Check API key is set:**

   ```bash
   echo $POPKIT_API_KEY
   ```

2. **Check hook is registered:**

   ```bash
   claude hooks list
   ```

3. **Test manually:**
   ```bash
   echo '{"tool_name":"Read","tool_input":{}}' | python agent-observability.py
   ```

### Connection Issues

The hook is designed to fail silently - it won't block your Claude Code session if the API is unreachable. Check the dashboard connection status indicator:

- 🟢 **Live (SSE)** - Real-time streaming active (Pro)
- 🔵 **Polling (3s)** - Polling mode active (Free)
- 🟡 **Connecting** - Establishing connection
- 🔴 **Error** - Connection failed

## Privacy

Events are scoped to your user account. We capture:

- Tool names and execution times
- Agent types and session IDs
- Error status (not error messages)

We do NOT capture:

- Tool inputs/outputs
- File contents
- Conversation history
- Personal data

See our [Privacy Policy](/privacy) for details.
