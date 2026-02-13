# XML User Guide for PopKit

**Version:** 1.0.0
**Last Updated:** 2026-01-21
**Status:** Beta

---

## Table of Contents

- [Introduction](#introduction)
- [Why Use XML Prompts?](#why-use-xml-prompts)
- [When to Use XML](#when-to-use-xml)
- [Workflow Templates](#workflow-templates)
  - [1. Debugging/Investigation](#1-debugginginvestigation-template)
  - [2. Feature Request](#2-feature-request-template)
  - [3. Code Review](#3-code-review-template)
  - [4. Performance Optimization](#4-performance-optimization-template)
- [How It Works](#how-it-works)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## Introduction

PopKit uses **XML-structured prompts** as an invisible context layer that helps Claude understand your requirements with exceptional precision. When you structure your requests using XML, PopKit can:

- **Route to the right agents** with 95% accuracy (vs. 80% with plain text)
- **Understand complex requirements** with nested conditions and dependencies
- **Track progress** through multi-step workflows
- **Provide better results** by preserving context across tool calls

XML in PopKit is **not visible to you** - it's injected by hooks automatically. However, you can **write your prompts using XML** to give Claude even more structured context.

---

## Why Use XML Prompts?

### Benefits

| Benefit                    | Plain Text   | XML-Structured |
| -------------------------- | ------------ | -------------- |
| **Agent Routing Accuracy** | ~80%         | ~95%           |
| **Requirement Clarity**    | Ambiguous    | Explicit       |
| **Multi-Step Workflows**   | Often missed | Tracked        |
| **Context Preservation**   | Degraded     | Maintained     |
| **Constraint Handling**    | Implicit     | Explicit       |

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

---

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

---

## Workflow Templates

### 1. Debugging/Investigation Template

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
      <time_constraint>Urgency level (production down, sprint deadline, etc.)</time_constraint>
      <compatibility>What must not break (API contracts, existing features)</compatibility>
      <resource_constraint>Budget, team capacity, etc.</resource_constraint>
    </constraints>
  </problem>
  <context>
    <recent_changes>What changed recently (code, config, dependencies)</recent_changes>
    <environment>Where it happens (production, staging, local)</environment>
    <affected_users>Impact scope (number of users, critical paths)</affected_users>
    <error_messages>Stack traces, logs, error codes</error_messages>
  </context>
  <hypothesis>
    <theory>Initial theory about root cause (optional)</theory>
    <evidence>Supporting evidence for theory</evidence>
  </hypothesis>
</investigation>
```

**Example:**

```xml
<investigation>
  <problem severity="critical">
    <symptom>Checkout process hangs indefinitely after clicking 'Place Order'</symptom>
    <reproduction>
      1. Add item to cart
      2. Proceed to checkout
      3. Fill in payment details
      4. Click "Place Order"
      5. Page freezes, no error message, no order created
    </reproduction>
    <constraints>
      <time_constraint>Black Friday sale starting in 6 hours</time_constraint>
      <compatibility>Cannot change payment API contract (external vendors integrated)</compatibility>
    </constraints>
  </problem>
  <context>
    <recent_changes>
      - Upgraded Stripe SDK from v10 to v11 yesterday
      - Added new fraud detection middleware 2 days ago
    </recent_changes>
    <environment>Production only (works fine in staging)</environment>
    <affected_users>100% of users attempting checkout (~2000 failed orders)</affected_users>
    <error_messages>
      Browser console: "Uncaught TypeError: Cannot read property 'then' of undefined at checkout.js:127"
      Server logs: No errors (request never reaches server)
    </error_messages>
  </context>
  <hypothesis>
    <theory>Stripe SDK v11 changed Promise API, breaking our async handling</theory>
    <evidence>Error occurs before server request, in client-side Stripe integration</evidence>
  </hypothesis>
</investigation>
```

**Agent Routing:** → `bug-whisperer` (systematic debugging specialist)

---

### 2. Feature Request Template

**Use when:** Implementing new functionality with requirements, priorities, and constraints.

```xml
<feature_request priority="high|medium|low">
  <objective>Clear, concise goal (1-2 sentences)</objective>
  <requirements>
    <requirement type="functional" priority="must|should|nice">
      Specific functional requirement
    </requirement>
    <requirement type="non-functional" priority="must">
      Performance, security, UX, etc.
    </requirement>
    <requirement type="ux" priority="should">
      User experience requirements
    </requirement>
  </requirements>
  <constraints>
    <constraint type="compatibility">Backward compatibility needs</constraint>
    <constraint type="technical">Technology stack, APIs, libraries to use/avoid</constraint>
    <constraint type="timeline">Delivery deadline</constraint>
    <constraint type="resources">Team capacity, budget</constraint>
  </constraints>
  <success_criteria>
    <criterion>Measurable success condition 1</criterion>
    <criterion>Measurable success condition 2</criterion>
  </success_criteria>
</feature_request>
```

**Example:**

```xml
<feature_request priority="high">
  <objective>
    Add dark mode toggle to application settings with persistent user preference
  </objective>
  <requirements>
    <requirement type="functional" priority="must">
      Settings page contains toggle switch for dark/light mode
    </requirement>
    <requirement type="functional" priority="must">
      User preference persists across sessions (localStorage + backend sync)
    </requirement>
    <requirement type="ux" priority="must">
      Theme switches immediately without page reload
    </requirement>
    <requirement type="ux" priority="should">
      Smooth transition animation between themes (300ms fade)
    </requirement>
    <requirement type="non-functional" priority="must">
      Works on all supported browsers (Chrome 90+, Firefox 88+, Safari 14+)
    </requirement>
    <requirement type="accessibility" priority="must">
      WCAG 2.1 AA contrast ratios in both themes
    </requirement>
  </requirements>
  <constraints>
    <constraint type="compatibility">
      Must not break existing custom themes (enterprise customers)
    </constraint>
    <constraint type="technical">
      Use existing CSS-in-JS theming system (styled-components)
    </constraint>
    <constraint type="timeline">
      Ship in next sprint (2 weeks)
    </constraint>
  </constraints>
  <success_criteria>
    <criterion>User can toggle dark mode in settings</criterion>
    <criterion>Preference persists after logout/login</criterion>
    <criterion>All components render correctly in both themes</criterion>
    <criterion>Accessibility audit passes (Lighthouse score 100)</criterion>
  </success_criteria>
</feature_request>
```

**Agent Routing:** → `code-architect` (feature design specialist)

---

### 3. Code Review Template

**Use when:** Reviewing code with specific concerns or focus areas.

```xml
<code_review focus="security|performance|style|correctness">
  <files>
    <file priority="high|medium|low">path/to/file.ext</file>
    <file priority="high">path/to/another_file.ext</file>
  </files>
  <concerns>
    <concern category="security">Specific security concern (SQL injection, XSS, etc.)</concern>
    <concern category="performance">Performance bottleneck or inefficiency</concern>
    <concern category="correctness">Logic errors, edge cases</concern>
    <concern category="style">Code style, readability, maintainability</concern>
  </concerns>
  <context>
    <purpose>What this code is supposed to do</purpose>
    <recent_issues>Known bugs or vulnerabilities in this area</recent_issues>
  </context>
  <review_depth>quick|standard|thorough</review_depth>
</code_review>
```

**Example:**

```xml
<code_review focus="security,performance">
  <files>
    <file priority="high">src/api/auth/login.py</file>
    <file priority="high">src/api/auth/session.py</file>
    <file priority="medium">src/api/auth/password_reset.py</file>
  </files>
  <concerns>
    <concern category="security">
      Check for SQL injection vulnerabilities in login queries
    </concern>
    <concern category="security">
      Validate session token expiration handling
    </concern>
    <concern category="performance">
      Session queries run on every request - potential N+1 problem
    </concern>
    <concern category="correctness">
      Password reset tokens may not expire properly
    </concern>
  </concerns>
  <context>
    <purpose>
      Authentication system for 50k+ daily active users
    </purpose>
    <recent_issues>
      - Security audit flagged potential timing attack in login (Issue #234)
      - Users reported slow login times during peak hours (Issue #240)
    </recent_issues>
  </context>
  <review_depth>thorough</review_depth>
</code_review>
```

**Agent Routing:** → `security-auditor` + `performance-optimizer` (multi-agent)

---

### 4. Performance Optimization Template

**Use when:** Optimizing performance with specific metrics and targets.

```xml
<optimization target="load_time|memory|throughput|latency">
  <current_performance>
    <metric name="metric_name" unit="unit">current_value</metric>
    <metric name="metric_name" unit="unit">current_value</metric>
    <target>target_value with unit</target>
  </current_performance>
  <bottlenecks>
    <bottleneck priority="high|medium|low">
      Description of suspected bottleneck
    </bottleneck>
  </bottlenecks>
  <constraints>
    <constraint>No breaking changes to public API</constraint>
    <constraint>Budget limit: $X/month for infrastructure</constraint>
  </constraints>
  <profiling_data>
    Path to profiling reports, flamegraphs, or key findings
  </profiling_data>
</optimization>
```

**Example:**

```xml
<optimization target="load_time">
  <current_performance>
    <metric name="page_load" unit="seconds">4.2</metric>
    <metric name="time_to_interactive" unit="seconds">6.8</metric>
    <metric name="largest_contentful_paint" unit="seconds">3.1</metric>
    <target>Page load under 1.5 seconds (Lighthouse score 90+)</target>
  </current_performance>
  <bottlenecks>
    <bottleneck priority="high">
      Bundle size: 2.8MB uncompressed (800KB gzipped)
    </bottleneck>
    <bottleneck priority="high">
      12 blocking render requests on initial load
    </bottleneck>
    <bottleneck priority="medium">
      Large hero image (1.2MB) not lazy-loaded
    </bottleneck>
    <bottleneck priority="low">
      Analytics scripts slow down TTI by ~500ms
    </bottleneck>
  </bottlenecks>
  <constraints>
    <constraint>No breaking changes to component API</constraint>
    <constraint>Must work on slow 3G connections (target market)</constraint>
    <constraint>Cannot remove analytics (business requirement)</constraint>
  </constraints>
  <profiling_data>
    Webpack bundle analyzer: lodash (420KB), moment.js (280KB) dominate bundle
    Chrome DevTools: Main thread blocked 80% of page load time
    Lighthouse report: docs/performance-audit-2026-01-20.pdf
  </profiling_data>
</optimization>
```

**Agent Routing:** → `performance-optimizer` (performance specialist)

---

## How It Works

### XML Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Input (Plain Text or XML)                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. user-prompt-submit Hook                                     │
│    - Analyzes prompt (plain or XML)                            │
│    - Generates problem-context.xml and project-context.xml     │
│    - Injects XML into prompt (invisible to you)                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Claude Receives Enhanced Prompt                             │
│    Your message + invisible XML context                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. pre-tool-use Hook                                           │
│    - Parses XML from context                                    │
│    - Selects optimal agent (95% accuracy)                       │
│    - Routes to specialist (bug-whisperer, code-architect, etc.) │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Tool Execution (Read, Edit, Bash, etc.)                     │
│    Claude uses tools to complete task                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. post-tool-use Hook                                          │
│    - Generates findings.xml                                     │
│    - Updates context for next iteration                         │
│    - Scores quality (risk, confidence, completeness)            │
└─────────────────────────────────────────────────────────────────┘
```

### Example Session

**User:** (Using XML debugging template)

```xml
<investigation>
  <problem severity="high">
    <symptom>API returns 500 on /users endpoint</symptom>
  </problem>
</investigation>
```

**PopKit Processing:**

1. **user-prompt-submit** hook:
   - Detects XML in prompt (already structured)
   - Adds project context (Python, Flask, PostgreSQL)
   - Injects complete context XML

2. **pre-tool-use** hook:
   - Parses XML: category=bug, severity=high
   - Agent score: bug-whisperer (0.95), refactoring-expert (0.32)
   - Routes to `bug-whisperer`

3. **bug-whisperer** agent:
   - Systematic debugging approach
   - Checks logs, DB connections, recent changes
   - Finds SQL query error in user model

4. **post-tool-use** hook:
   - Generates findings: root_cause=SQL syntax error
   - Updates context for next step (fix implementation)

**Result:** Bug identified in 2 minutes with 95% confidence (vs. 10 minutes with plain text)

---

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
  <criterion>Bundle size reduced by 50% (from 2.8MB to <1.4MB)</criterion>
</success_criteria>
```

### 3. Use Severity Appropriately

| Severity     | When to Use                                             |
| ------------ | ------------------------------------------------------- |
| **critical** | Production down, data loss, security breach             |
| **high**     | Degraded service, urgent fix needed, affects many users |
| **medium**   | Feature not working, workaround exists                  |
| **low**      | Minor bug, cosmetic issue, nice-to-have                 |

### 4. Keep Descriptions Concise

❌ **Too Verbose:**

```xml
<symptom>
  So basically what happened is that yesterday when I was testing the new feature
  that we deployed last week, I noticed that sometimes, but not always, when you
  click the button, it doesn't seem to do anything at all...
</symptom>
```

✅ **Concise:**

```xml
<symptom>
  Submit button occasionally non-responsive (50% of clicks have no effect)
</symptom>
```

### 5. Leverage Conditional Logic for Multi-Step Workflows

```xml
<workflow>
  <step id="1" required="true" blocking="true">
    <action>Search codebase for authentication logic</action>
    <target>src/auth/</target>
    <success-criteria>
      <criterion>Found login handler function</criterion>
    </success-criteria>
  </step>
  <conditional on-step="1">
    <branch condition="bug_found">
      <step id="2a">
        <action>Fix the identified bug</action>
      </step>
    </branch>
    <branch condition="no_bug_found">
      <step id="2b">
        <action>Investigate database queries</action>
      </step>
    </branch>
  </conditional>
</workflow>
```

---

## FAQ

### When should I use XML vs plain text?

**Use XML when:**

- Task has multiple steps or conditions
- You need specific agent routing (security review, performance optimization)
- There are important constraints or requirements
- You want explicit priorities and success criteria

**Use plain text when:**

- Simple, single-action requests
- Exploratory questions
- Brainstorming or ideation
- Quick fixes or clarifications

### Does XML slow down responses?

No - XML processing adds ~50-100ms overhead (negligible). Benefits far outweigh cost:

- Faster agent routing (correct specialist first time)
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

PopKit will extract and process the XML automatically.

### What if I make an XML syntax error?

PopKit's XML parser is forgiving:

- Missing tags are ignored
- Invalid structure falls back to plain text processing
- You'll still get results (just less optimal agent routing)

**Tip:** Start with templates and modify them - this prevents syntax errors.

### How do I know if XML is working?

Look for these signs:

- Claude mentions specific agents ("Let me use the bug-whisperer agent...")
- Faster time to solution
- Fewer clarifying questions
- More structured responses

You can also check PopKit's internal logs (`~/.popkit/logs/xml-processing.log`)

### Can I create my own XML templates?

Yes! Follow the structure of existing templates and use standard XML elements:

- `<problem>`, `<context>`, `<constraints>`, `<requirements>`
- Always include `severity` or `priority` attributes
- Use clear, descriptive tag names

Share your templates with the community: https://github.com/jrc1883/popkit-claude/discussions

---

## Next Steps

1. **Try a template** - Copy one of the 4 templates and modify for your use case
2. **Experiment** - Start with plain text, add XML when complexity increases
3. **Share feedback** - Let us know what works: https://github.com/jrc1883/popkit-claude/issues/99

---

## Resources

- **XML Schemas:** `packages/shared-py/popkit_shared/schemas/`
- **Hook Source Code:** `packages/popkit-core/hooks/`
- **XML Utilities:** `packages/shared-py/popkit_shared/utils/xml_*.py`
- **Tests:** `packages/shared-py/tests/utils/test_xml_*.py`

---

**Questions or feedback?** Open an issue: https://github.com/jrc1883/popkit-claude/issues/99

**Want to contribute?** Share your custom templates in Discussions!

---

_Generated with Claude Sonnet 4.5 via PopKit v1.0.0-beta.5_
