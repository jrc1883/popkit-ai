---
title: XML Prompts Guide
description: Master structured prompting for precise agent routing and better results
---

# XML Prompts Guide

PopKit uses **XML-structured prompts** as an invisible context layer that helps Claude understand your requirements with exceptional precision. When you structure your requests using XML, PopKit can:

- **Route to the right agents** with 95% accuracy (vs. 80% with plain text)
- **Understand complex requirements** with nested conditions and dependencies
- **Track progress** through multi-step workflows
- **Provide better results** by preserving context across tool calls

XML in PopKit is **not visible to you** - it's injected by hooks automatically. However, you can **write your prompts using XML** to give Claude even more structured context.

## Why Use XML Prompts?

### Benefits

| Benefit | Plain Text | XML-Structured |
|---------|-----------|----------------|
| **Agent Routing Accuracy** | ~80% | ~95% |
| **Requirement Clarity** | Ambiguous | Explicit |
| **Multi-Step Workflows** | Often missed | Tracked |
| **Context Preservation** | Degraded | Maintained |
| **Constraint Handling** | Implicit | Explicit |

### Real-World Example

**Plain Text Prompt:**
> "The login is broken, fix it"

**Issues:**
- What kind of broken? (500 error? UI issue? Performance?)
- Where is the code? (Which files?)
- What's the urgency? (Production down? Minor bug?)
- What are the constraints? (Can we change the DB schema?)

**XML Prompt:**
```xml
<investigation>
  <problem severity="high">
    <symptom>Login fails with 500 Internal Server Error</symptom>
    <reproduction>
      1. Navigate to /login
      2. Enter valid credentials
      3. Click submit
      4. Observe 500 error in console
    </reproduction>
    <constraints>
      <time_constraint>Production issue, urgent fix needed</time_constraint>
      <compatibility>Cannot break existing sessions</compatibility>
    </constraints>
  </problem>
  <context>
    <recent_changes>Updated auth library from 2.1 to 3.0 yesterday</recent_changes>
    <environment>Production (reproducible in staging)</environment>
    <affected_users>~500 users unable to log in</affected_users>
  </context>
</investigation>
```

**Result:** Claude immediately knows:
- Severity: HIGH (production down)
- Root cause area: Auth library upgrade
- Constraints: Can't break existing sessions, urgent
- Agent routing: → `bug-whisperer` (not `refactoring-expert`)

## When to Use XML

### Use XML For:

✅ **Complex debugging** - Multiple symptoms, unclear root cause, constraints
✅ **Feature requests** - Requirements with priorities, dependencies, constraints
✅ **Code reviews** - Specific focus areas (security, performance, style)
✅ **Performance optimization** - Metrics, targets, bottlenecks
✅ **Multi-step workflows** - Conditional logic, parallel tasks, dependencies

### Use Plain Text For:

✅ **Simple questions** - "What does this function do?"
✅ **Quick fixes** - "Fix the typo in README line 42"
✅ **Exploratory conversations** - "Tell me about this codebase"
✅ **Brainstorming** - "Ideas for improving UX?"

## Workflow Templates

### 1. Debugging/Investigation

**Use when:** You have a bug with unclear root cause, multiple symptoms, or constraints.

```xml
<investigation>
  <problem severity="high|medium|low">
    <symptom>Clear description of observable issue</symptom>
    <reproduction>
      Step-by-step reproduction:
      1. Action 1
      2. Action 2
      3. Observe issue
    </reproduction>
    <constraints>
      <time_constraint>Urgency level</time_constraint>
      <compatibility>What must not break</compatibility>
    </constraints>
  </problem>
  <context>
    <recent_changes>What changed recently</recent_changes>
    <environment>Where it happens</environment>
    <affected_users>Impact scope</affected_users>
    <error_messages>Stack traces, logs</error_messages>
  </context>
  <hypothesis>
    <theory>Initial theory about root cause</theory>
    <evidence>Supporting evidence</evidence>
  </hypothesis>
</investigation>
```

### 2. Feature Request

**Use when:** Implementing new functionality with requirements, priorities, and constraints.

```xml
<feature_request priority="high|medium|low">
  <objective>Clear, concise goal (1-2 sentences)</objective>
  <requirements>
    <requirement type="functional" priority="must|should|nice">
      Specific functional requirement
    </requirement>
    <requirement type="non-functional" priority="must">
      Performance, security, UX requirements
    </requirement>
  </requirements>
  <constraints>
    <constraint type="compatibility">Compatibility needs</constraint>
    <constraint type="technical">Tech stack constraints</constraint>
    <constraint type="timeline">Delivery deadline</constraint>
  </constraints>
  <success_criteria>
    <criterion>Measurable success condition 1</criterion>
    <criterion>Measurable success condition 2</criterion>
  </success_criteria>
</feature_request>
```

### 3. Code Review

**Use when:** Reviewing code with specific concerns or focus areas.

```xml
<code_review focus="security|performance|style|correctness">
  <files>
    <file priority="high">path/to/file.ext</file>
    <file priority="medium">path/to/another_file.ext</file>
  </files>
  <concerns>
    <concern category="security">Specific security concern</concern>
    <concern category="performance">Performance bottleneck</concern>
    <concern category="correctness">Logic errors, edge cases</concern>
  </concerns>
  <context>
    <purpose>What this code does</purpose>
    <recent_issues>Known bugs or vulnerabilities</recent_issues>
  </context>
  <review_depth>quick|standard|thorough</review_depth>
</code_review>
```

### 4. Performance Optimization

**Use when:** Optimizing performance with specific metrics and targets.

```xml
<optimization target="load_time|memory|throughput|latency">
  <current_performance>
    <metric name="page_load" unit="seconds">4.2</metric>
    <metric name="time_to_interactive" unit="seconds">6.8</metric>
    <target>Page load under 1.5 seconds</target>
  </current_performance>
  <bottlenecks>
    <bottleneck priority="high">
      Bundle size: 2.8MB uncompressed
    </bottleneck>
    <bottleneck priority="medium">
      Large images not lazy-loaded
    </bottleneck>
  </bottlenecks>
  <constraints>
    <constraint>No breaking API changes</constraint>
    <constraint>Must work on 3G connections</constraint>
  </constraints>
  <profiling_data>
    Path to profiling reports or key findings
  </profiling_data>
</optimization>
```

## How It Works

### XML Processing Pipeline

```
┌─────────────────────────────────────────────────────┐
│ 1. User Input (Plain Text or XML)                  │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────┐
│ 2. user-prompt-submit Hook                         │
│    - Analyzes prompt                                │
│    - Generates context XML                          │
│    - Injects into prompt (invisible)                │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────┐
│ 3. Claude Receives Enhanced Prompt                  │
│    Your message + invisible XML context             │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────┐
│ 4. pre-tool-use Hook                                │
│    - Parses XML                                     │
│    - Selects optimal agent (95% accuracy)           │
│    - Routes to specialist                           │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────┐
│ 5. Tool Execution                                   │
│    Claude completes task                            │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────┐
│ 6. post-tool-use Hook                               │
│    - Generates findings                             │
│    - Updates context for next iteration             │
└─────────────────────────────────────────────────────┘
```

## Best Practices

### 1. Be Specific with Constraints

❌ **Vague:**
```xml
<constraint>Fix it fast</constraint>
```

✅ **Specific:**
```xml
<constraint type="timeline">Fix must deploy by 5pm today (production hotfix window)</constraint>
```

### 2. Include Success Criteria

❌ **Vague:**
```xml
<objective>Make the app faster</objective>
```

✅ **Measurable:**
```xml
<objective>Reduce page load time from 4.2s to under 1.5s (Lighthouse score 90+)</objective>
<success_criteria>
  <criterion>Lighthouse Performance score ≥ 90</criterion>
  <criterion>Time to Interactive (TTI) < 2.0 seconds</criterion>
</success_criteria>
```

### 3. Use Severity Appropriately

| Severity | When to Use |
|----------|-------------|
| **critical** | Production down, data loss, security breach |
| **high** | Degraded service, urgent fix needed |
| **medium** | Feature not working, workaround exists |
| **low** | Minor bug, cosmetic issue |

### 4. Keep Descriptions Concise

❌ **Too Verbose:**
```xml
<symptom>
  So basically what happened is that yesterday when I was testing...
</symptom>
```

✅ **Concise:**
```xml
<symptom>
  Submit button occasionally non-responsive (50% of clicks)
</symptom>
```

## FAQ

### When should I use XML vs plain text?

**Use XML when:**
- Task has multiple steps or conditions
- You need specific agent routing
- There are important constraints
- You want explicit priorities

**Use plain text when:**
- Simple, single-action requests
- Exploratory questions
- Brainstorming
- Quick fixes

### Does XML slow down responses?

No - XML processing adds ~50-100ms overhead (negligible). Benefits far outweigh cost:
- Faster agent routing
- Fewer clarifying questions
- Higher quality results
- Less back-and-forth

### Can I mix XML and plain text?

Yes! You can embed XML snippets in plain text prompts:

```
Hey Claude, I need help with a bug.

<investigation>
  <problem severity="high">
    <symptom>Login fails with 500 error</symptom>
  </problem>
</investigation>

Can you help me debug this?
```

### What if I make an XML syntax error?

PopKit's XML parser is forgiving:
- Missing tags are ignored
- Invalid structure falls back to plain text
- You'll still get results (just less optimal routing)

**Tip:** Start with templates and modify them to prevent syntax errors.

### How do I know if XML is working?

Look for these signs:
- Claude mentions specific agents
- Faster time to solution
- Fewer clarifying questions
- More structured responses

## Next Steps

1. **Try a template** - Copy one of the templates and modify for your use case
2. **Experiment** - Start with plain text, add XML when complexity increases
3. **Share feedback** - Let us know what works via GitHub issues

## Resources

- [GitHub Repository](https://github.com/jrc1883/popkit-claude)
- [Issue Tracker](https://github.com/jrc1883/popkit-claude/issues)
- [XML User Guide (Full Version)](https://github.com/jrc1883/popkit-claude/blob/main/packages/popkit-core/XML-USER-GUIDE.md)
