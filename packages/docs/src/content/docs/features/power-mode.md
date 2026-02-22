---
title: Power Mode
description: Multi-agent orchestration for complex workflows
---

# Power Mode

Power Mode enables parallel agent collaboration for complex tasks requiring multiple specialized agents working together.

## What is Power Mode?

Power Mode orchestrates multiple agents simultaneously to tackle complex workflows that would be too slow or cumbersome with a single agent.

**Use Cases**:

- Large-scale refactoring across many files
- Comprehensive security audits
- Multi-component feature development
- Architecture analysis and migration

## Modes of Operation

### Native Async Mode (Recommended)

**Requirements**: Claude Code 2.1.33+

**Features**:

- Zero setup required
- 5+ agents via Background Task tool
- Event-driven agent lifecycle management
- Graceful shutdown with configurable timeout
- Action tracking for dashboard state
- Best for most use cases

**Activation**:

```bash
/popkit-core:power start
```

### Redis Mode (Advanced)

**Requirements**: Redis server, Claude Code 2.1.33+

**Features**:

- 10+ agents with persistent coordination
- Best for very complex workflows
- Requires Redis setup

**Setup**:

```bash
# Install Redis
# Configure connection in .popkit/config.json

/popkit-core:power start --redis
```

### File-Based Mode (Legacy)

**Requirements**: None

**Features**:

- 2 agents sequential
- Fallback for older Claude Code versions
- No external dependencies

**Activation**: Automatic fallback

## Using Power Mode

### 1. Check Status

```bash
/popkit-core:power status
```

This shows:

- Current mode (Native/Redis/File)
- Active agents
- Performance metrics

### 2. Start Power Mode

```bash
/popkit-core:power start
```

### 3. Run Workflows

```bash
# Feature development with multiple agents
/popkit-dev:dev "Implement OAuth2" --power

# Comprehensive security audit
/popkit-ops:security scan --power

# Architecture analysis
/popkit-core:project analyze --power
```

### 4. Monitor Progress

```bash
/popkit-core:power metrics
```

Shows:

- Agents active
- Tasks in progress
- Completion status

### 5. Stop Power Mode

```bash
/popkit-core:power stop
```

## Performance Comparison

| Mode             | Agents | Setup | Use Case                     |
| ---------------- | ------ | ----- | ---------------------------- |
| **Native Async** | 5+     | None  | Most workflows (recommended) |
| **Redis**        | 10+    | Redis | Very complex workflows       |
| **File-Based**   | 2      | None  | Simple workflows, legacy     |

## Best Practices

1. **Start with Native Async**: Works for 95% of use cases
2. **Use Redis for Scale**: Only when you need 10+ agents
3. **Monitor Performance**: Check metrics to optimize
4. **Stop When Done**: Free resources after completion

## Troubleshooting

### Power Mode Won't Start

**Symptom**: `power start` fails

**Solutions**:

- Check Claude Code version (need 2.1.33+)
- Verify Redis is running (for Redis mode)
- Check logs: `/popkit-core:power status --verbose`

### Agents Not Responding

**Symptom**: Tasks stuck in progress

**Solutions**:

- Check individual agent logs
- Restart Power Mode
- Reduce agent count

### Performance Issues

**Symptom**: Slow responses

**Solutions**:

- Switch to Native Async mode
- Reduce concurrent agents
- Check system resources

## Next Steps

- Learn about [Feature Development](/features/feature-dev/)
- Explore [Git Workflows](/features/git-workflows/)
- Understand [Routines](/features/routines/)
